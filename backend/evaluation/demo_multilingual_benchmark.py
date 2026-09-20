"""Synthetic, non-patient Groq comparison for IAMINA public demo."""
import argparse, json, os
from pathlib import Path
from openai import OpenAI

MODELS=["openai/gpt-oss-120b","allam-2-7b"]
PROMPTS=[
("darija-latin","fia doukha"),("darija-latin","ma fhemtch chno glti"),
("darija-latin","3ndi sda3 mn sba7"),("darija-latin","wach t9der tchra7 lia hadchi b darija?"),
("darija-latin","kan7ess brassi 3yan bezaf lyouma"),("darija-ar","شنو نقدر ندير باش نفهم هاد النتيجة؟"),
("darija-ar","عندي الدوخة من الصباح"),("darija-ar","واش تقدر تشرح ليا بالدارجة؟"),
("english","I feel dizzy today."),("english","Can you explain this in simple English?"),
("english","What languages can you speak?"),("gulf","وش فيني أحس بدوخة اليوم"),
("gulf","ممكن تشرح لي بطريقة أبسط؟"),("gulf","أنا تعبان شوي اليوم وش أسوي؟"),
("gulf","تقدر تكلمني باللهجة الخليجية؟")]
SYSTEM="""You are IAmina in PUBLIC DEMO mode. You have NO patient record, memory, clinical measurements or identity.
Infer the language from the current message only. English stays English; French stays French; MSA stays MSA; Moroccan Darija stays Darija; recognizable Gulf Arabic stays in the same Gulf variety when practical. Never switch to Darija because examples mention it. Switch languages only if explicitly asked.
For Moroccan Darija, use natural everyday wording and mirror Latin/Arabic script. For symptoms acknowledge and ask at most one useful non-diagnostic follow-up. Never diagnose, prescribe, calculate doses, change treatment, invent patient facts, or claim dossier access. Keep under 80 words."""
def main():
 p=argparse.ArgumentParser(); p.add_argument("--output",required=True); a=p.parse_args()
 key=os.environ.get("GROQ_API_KEY"); 
 if not key: raise SystemExit("GROQ_API_KEY missing")
 c=OpenAI(base_url="https://api.groq.com/openai/v1",api_key=key,timeout=20,max_retries=0)
 rows=[]
 for model in MODELS:
  for locale,prompt in PROMPTS:
   try:
    r=c.chat.completions.create(model=model,messages=[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],max_tokens=180)
    rows.append({"model":model,"locale":locale,"prompt":prompt,"reply":r.choices[0].message.content or "","error":None})
   except Exception as e:
    rows.append({"model":model,"locale":locale,"prompt":prompt,"reply":"","error":type(e).__name__+": "+str(e)[:300]})
 out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps({"synthetic":True,"models":MODELS,"rows":rows},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
