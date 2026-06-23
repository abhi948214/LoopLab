require('dotenv').config();

const express = require('express');
const cors = require('cors');
const path = require('path');
const OpenAI = require('openai');

const app = express();
const PORT = process.env.PORT || 3000;

const openai = process.env.OPENAI_API_KEY
  ? new OpenAI({ apiKey: process.env.OPENAI_API_KEY })
  : null;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '..')));

const PROMPTS = {
  caption: (data) =>
    `Write an Instagram caption for a post about "${data.topic}". ` +
    `Tone: ${data.tone || 'friendly'}. ` +
    `Length: ${data.length || 'medium'} (short=1-2 sentences, medium=3-5 sentences, long=6+ sentences). ` +
    `Include relevant emojis. Do not include hashtags in the caption.`,

  hashtags: (data) =>
    `Generate 20-30 relevant Instagram hashtags for a post about "${data.topic}" ` +
    `in the ${data.niche || 'general'} niche. ` +
    `Mix popular and niche-specific tags. Return only hashtags separated by spaces, no other text.`,

  bio: (data) =>
    `Write a compelling Instagram bio (max 150 characters) for someone who is a ${data.profession || 'creator'} ` +
    `interested in ${data.interests || 'lifestyle'}. ` +
    `Style: ${data.style || 'professional yet approachable'}. Include a subtle call-to-action if space allows.`,

  ideas: (data) =>
    `Generate 8 creative Instagram post or Reel ideas for a ${data.niche || 'lifestyle'} account ` +
    `targeting ${data.audience || 'general audience'}. ` +
    `Format as a numbered list. Each idea should be one line with a brief hook.`,
};

async function generate(tool, input) {
  if (!openai) {
    throw new Error(
      'OpenAI API key not configured. Copy .env.example to .env and add your OPENAI_API_KEY.'
    );
  }

  const prompt = PROMPTS[tool](input);

  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'system',
        content:
          'You are an expert Instagram content strategist. Write engaging, authentic content that performs well on Instagram.',
      },
      { role: 'user', content: prompt },
    ],
    max_tokens: 600,
    temperature: 0.8,
  });

  return response.choices[0]?.message?.content?.trim() || 'No content generated.';
}

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, aiConfigured: Boolean(openai) });
});

app.post('/api/generate/:tool', async (req, res) => {
  const { tool } = req.params;
  const validTools = ['caption', 'hashtags', 'bio', 'ideas'];

  if (!validTools.includes(tool)) {
    return res.status(400).json({ error: 'Invalid tool. Use: caption, hashtags, bio, or ideas.' });
  }

  const { topic, tone, length, niche, profession, interests, style, audience } = req.body;

  if (!topic && tool !== 'bio') {
    return res.status(400).json({ error: 'Topic is required.' });
  }

  if (tool === 'bio' && !profession && !interests) {
    return res.status(400).json({ error: 'Profession or interests is required for bio generation.' });
  }

  try {
    const result = await generate(tool, {
      topic,
      tone,
      length,
      niche,
      profession,
      interests,
      style,
      audience,
    });
    res.json({ result });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message || 'Generation failed.' });
  }
});

app.listen(PORT, () => {
  console.log(`LoopLAB Instagram AI running at http://localhost:${PORT}`);
  console.log(`AI configured: ${Boolean(openai)}`);
});
