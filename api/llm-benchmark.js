const ENDPOINT = 'https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions';

const DEFAULT_MODELS = [
  'gpt-oss-120b',
  'mistral@latest',
  'llama@biggest?input_cost<0.5',
  'code_chat@latest'
];

const SYNTHETIC_MESSAGES = [
  {
    role: 'system',
    content: 'Tu es un assistant conversationnel de santé non diagnostique. Réponds avec naturel, concision, empathie sobre, sans inventer et dans la langue du dernier message. Données entièrement synthétiques.'
  },
  {
    role: 'user',
    content: 'Je m’appelle Samir, j’ai 42 ans. Je veux surtout comprendre mes habitudes et poser des questions simples, pas recevoir un diagnostic.'
  },
  {
    role: 'assistant',
    content: 'Compris. Je peux t’aider à clarifier tes habitudes et tes questions, sans poser de diagnostic.'
  },
  {
    role: 'user',
    content: 'دابا إلى نسيت شنو قلت ليك قبل شوية، واش تقدر تذكرني بالعمر ديالي وباش بغيت نستعمل هاد الشات؟ جاوبني بالدارجة المغربية وبشكل طبيعي.'
  }
];

async function callModel(model, messages) {
  const started = Date.now();
  const response = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'accept': 'application/json' },
    body: JSON.stringify({ model, messages, temperature: 0.4, max_tokens: 220 })
  });
  const elapsed_ms = Date.now() - started;
  const raw = await response.text();
  let data;
  try { data = JSON.parse(raw); } catch { data = { raw }; }
  return {
    model_requested: model,
    status: response.status,
    ok: response.ok,
    elapsed_ms,
    model_resolved: data?.model || null,
    text: data?.choices?.[0]?.message?.content || null,
    usage: data?.usage || null,
    error: response.ok ? null : data
  };
}

module.exports = async function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json({
      purpose: 'temporary IAMINA synthetic LLM benchmark',
      provider: 'OVHcloud AI Endpoints anonymous access',
      models: DEFAULT_MODELS,
      no_patient_data: true,
      note: 'Temporary benchmark endpoint. No secrets are stored.'
    });
  }
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const requested = Array.isArray(req.body?.models) && req.body.models.length
    ? req.body.models.slice(0, 4)
    : DEFAULT_MODELS;
  const messages = Array.isArray(req.body?.messages) && req.body.messages.length
    ? req.body.messages
    : SYNTHETIC_MESSAGES;

  const results = [];
  for (const model of requested) {
    try { results.push(await callModel(model, messages)); }
    catch (e) { results.push({ model_requested: model, ok: false, error: String(e) }); }
  }
  return res.status(200).json({ generated_at: new Date().toISOString(), synthetic_only: true, results });
};
