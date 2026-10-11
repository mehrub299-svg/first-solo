const STOPWORDS = new Set([
  "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
  "has", "have", "had", "not", "but", "its", "their", "they", "you", "your",
  "what", "when", "where", "which", "who", "how", "why", "can", "will", "does",
  "did", "about", "into", "than", "then", "there", "these", "those", "been",
  "also", "such", "each", "per", "use", "used", "uses", "one",
]);

function tokenize(text) {
  const words = text.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];
  return words.filter((word) => word.length >= 3 && !STOPWORDS.has(word));
}

// True when the model (or backend) says nothing in the documents answers the question.
export function isNoAnswer(answer) {
  const normalized = answer.replace(/[\u2018\u2019]/g, "'").toLowerCase();
  return normalized.includes("i don't know based on the provided documents");
}

// Splits a passage into segments and marks the sentence(s) that share the most
// words with the answer. A visual guide only: the API does not return exact spans.
export function highlightSegments(content, answer) {
  const whole = [{ text: content, mark: false }];

  const pieces = content.match(/[^.!?\u0964\n]+[.!?\u0964]*\s*|\n+/g);
  if (!pieces || pieces.join("") !== content) return whole;

  const answerTokens = new Set(
    tokenize(answer.replace(/\[\d+(?:\s*,\s*\d+)*\]/g, " ")),
  );
  if (answerTokens.size === 0) return whole;

  const scores = pieces.map((piece) => {
    let score = 0;
    for (const word of new Set(tokenize(piece))) {
      if (answerTokens.has(word)) score += 1;
    }
    return score;
  });

  const best = Math.max(...scores);
  const minScore = Math.min(2, answerTokens.size);
  if (best < minScore) return whole;

  const marked = new Set();
  scores.forEach((score, index) => {
    if (score === best && marked.size < 2) marked.add(index);
  });

  const segments = [];
  pieces.forEach((piece, index) => {
    if (!marked.has(index)) {
      segments.push({ text: piece, mark: false });
      return;
    }
    const core = piece.trimEnd();
    segments.push({ text: core, mark: true });
    if (core.length < piece.length) {
      segments.push({ text: piece.slice(core.length), mark: false });
    }
  });
  return segments;
}