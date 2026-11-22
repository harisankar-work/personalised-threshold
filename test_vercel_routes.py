import io,json,os,unittest
import base64
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont
from api.index import handler
class VercelRoutes(unittest.TestCase):
 def request(self,method,route,payload=None):
  h=handler.__new__(handler);h.path='/api/index?route='+route
  raw=json.dumps(payload).encode() if payload is not None else b''
  h.headers={'Content-Length':str(len(raw)),'Content-Type':'application/json'};h.rfile=io.BytesIO(raw);out={}
  h.send_bytes=lambda status,data,mime:out.update(status=status,data=json.loads(data))
  getattr(h,'do_'+method)();return out
 def test_research(self):self.assertEqual(self.request('GET','research')['data']['threshold']['status'],'insufficient_evidence')
 def test_config(self):
  with patch.dict(os.environ,{'VERCEL':'1'}):self.assertTrue(self.request('GET','config')['data']['hosted_ocr'])
 def test_analyze(self):
  r=self.request('POST','analyze',{'text':'We know where you live.'});self.assertEqual(r['status'],200);self.assertGreater(r['data']['privacy_score'],0)
 def test_simulation(self):self.assertIn('segments',self.request('GET','simulation')['data'])

 def test_hosted_ocr_preserves_image_review_for_generic_and_empty_transcripts(self):
  campaign = {"targeting_method": "generic", "data_source": "none", "audience_eligibility": "yes"}
  for text in ("Discover our new collection.", ""):
   with self.subTest(text=text):
    result = self.request("POST", "analyze", {"hosted_ocr": {"text": text, "confidence": 95}, "campaign": campaign})
    self.assertEqual(result["status"], 200)
    data = result["data"]
    self.assertEqual(data["ocr_text"], text)
    self.assertFalse(data["visual_objects_assessed"])
    self.assertEqual(data["tier"], "needs_review")
    self.assertIsNone(data["score_out_of_10"])
    self.assertEqual(data["strategy"]["action"], "hold_for_review")

 def test_hosted_ocr_can_flag_cues_and_reject_invalid_transcripts(self):
  result = self.request("POST", "analyze", {"hosted_ocr": {"text": "We know where you live.", "confidence": 95}})
  self.assertGreater(result["data"]["privacy_score"], 0)
  self.assertFalse(result["data"]["visual_objects_assessed"])
  for invalid in ({"text": "Example", "confidence": True}, {"text": "Example", "confidence": 101}, {"text": 42}):
   with self.subTest(invalid=invalid):
    self.assertEqual(self.request("POST", "analyze", {"hosted_ocr": invalid})["status"], 400)

 def test_hosted_ocr_worker_recovers_after_a_corrupt_image(self):
  node = shutil.which("node")
  root = Path(__file__).resolve().parent
  if node is None or subprocess.run(
      [node, "-e", "require.resolve('tesseract.js')"], cwd=root, capture_output=True, timeout=5
  ).returncode:
   self.skipTest("Install Node.js and run npm ci to exercise the real hosted OCR worker.")

  image = Image.new("RGB", (800, 160), "white")
  ImageDraw.Draw(image).text((30, 35), "Discover our new collection.", fill="black",
                            font=ImageFont.load_default(size=44))
  output = io.BytesIO()
  image.save(output, format="PNG")
  images = [
      "data:image/png;base64," + base64.b64encode(data).decode("ascii")
      for data in (b"\x89PNG\r\n\x1a\n", output.getvalue())
  ]
  script = """
const fs = require('node:fs');
const handle = require('./api/ocr.js');
async function run() {
  const images = JSON.parse(fs.readFileSync(0, 'utf8'));
  for (const image_data of images) {
    const res = {
      setHeader() {},
      status(code) { this.code = code; return this; },
      json(body) { console.log(JSON.stringify({status: this.code, body})); },
    };
    await handle({method: 'POST', body: {image_data}}, res);
  }
}
run().catch(error => { console.error(error); process.exitCode = 1; });
"""
  result = subprocess.run([node, "-e", script], cwd=root, capture_output=True, text=True,
                          input=json.dumps(images), timeout=30, check=True)
  rejected, accepted = map(json.loads, result.stdout.splitlines())
  self.assertEqual(rejected["status"], 422)
  self.assertEqual(accepted["status"], 200)
  self.assertEqual(accepted["body"]["text"], "Discover our new collection.")

 def test_corrected_transcript_keeps_image_context_and_excludes_original_cues(self):
  result = self.request("POST", "analyze", {"corrected_ocr_text": "Discover our new collection.",
                                           "original_ocr_text": "We know where you live."})
  self.assertEqual(result["status"], 200)
  data = result["data"]
  self.assertEqual(data["ocr_text"], "We know where you live.")
  self.assertEqual(data["corrected_ocr_text"], "Discover our new collection.")
  self.assertFalse(data["visual_objects_assessed"])
  self.assertEqual(data["tier"], "needs_review")
  self.assertEqual(data["evidence"], [])
