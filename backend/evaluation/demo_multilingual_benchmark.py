"""Synthetic, non-patient benchmark through the exact IAMINA demo model path."""
import argparse, json, os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "amina.settings")
os.environ["IAMINA_DEMO_EXTERNAL_AI_ENABLED"] = "true"
os.environ["IAMINA_DEMO_LLM_PROVIDER"] = "groq"

import django
django.setup()

from companion.demo_model import generate_demo_reply

MODELS=["openai/gpt-oss-120b","allam-2-7b"]
PROMPTS=[
("darija-latin","fr","fia doukha"),("darija-latin","fr","ma fhemtch chno glti"),
("darija-latin","fr","3ndi sda3 mn sba7"),("darija-latin","fr","wach t9der tchra7 lia hadchi b darija?"),
("darija-latin","fr","kan7ess brassi 3yan bezaf lyouma"),("darija-ar","ar-MA","شنو نقدر ندير باش نفهم هاد النتيجة؟"),
("darija-ar","ar-MA","عندي الدوخة من الصباح"),("darija-ar","ar-MA","واش تقدر تشرح ليا بالدارجة؟"),
("english","en","I feel dizzy today."),("english","en","Can you explain this in simple English?"),
("english","en","What languages can you speak?"),("gulf","ar","وش فيني أحس بدوخة اليوم"),
("gulf","ar","ممكن تشرح لي بطريقة أبسط؟"),("gulf","ar","أنا تعبان شوي اليوم وش أسوي؟"),
("gulf","ar","تقدر تكلمني باللهجة الخليجية؟")]
def main():
 p=argparse.ArgumentParser(); p.add_argument("--output",required=True); a=p.parse_args()
 if not os.environ.get("GROQ_API_KEY"): raise SystemExit("GROQ_API_KEY missing")
 rows=[]
 for model in MODELS:
  os.environ["IAMINA_DEMO_LLM_MODEL"]=model
  for locale,language,prompt in PROMPTS:
   try:
    reply=generate_demo_reply(prompt,language)
    rows.append({"model":model,"locale":locale,"prompt":prompt,"reply":reply,"error":None})
   except Exception as e:
    rows.append({"model":model,"locale":locale,"prompt":prompt,"reply":"","error":type(e).__name__+": "+str(e)[:300]})
 out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps({"synthetic":True,"production_path":True,"models":MODELS,"rows":rows},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
