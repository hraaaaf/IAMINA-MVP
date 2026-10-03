const BACKEND = "https://iamina-certified-79hw727il-achraf-benmoussa-s-projects.vercel.app";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({detail: "Method not allowed"});
  }
  try {
    const upstream = await fetch(
      `${BACKEND}/api/v1/demo/chat?_vercel_share=iH6GgzjTKOc0GemaB5F0jXeuDIH3DpRD`,
      {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(req.body ?? {}),
      },
    );
    const text = await upstream.text();
    const contentType = upstream.headers.get("content-type");
    if (contentType) res.setHeader("content-type", contentType);
    return res.status(upstream.status).send(text);
  } catch (error) {
    return res.status(502).json({detail: "Intent preview backend unavailable"});
  }
}
