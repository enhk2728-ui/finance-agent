---
name: humanize-chinese
description: Detect and rewrite AI-sounding Chinese text to natural, human-like expression. Use when the user says "make it sound human", "去掉AI味", "润色成真人风格", or when Chinese output sounds stiff/translated.
---

# Humanize Chinese

## When to Use
- User asks to humanize/rewrite Chinese text
- Chinese output sounds robotic, translated, or AI-generated
- Posts/articles/emails need natural Chinese voice

## Detection Patterns (AI-sounding)

| Pattern | Example | Fix |
|---------|---------|-----|
| 首先/其次/最后/总而言之 | 总而言之，这是一个很好的方案 | Delete or collapse to one natural transition |
| 值得注意的是 | 值得注意的是... | Drop entirely, just state the point |
| 此外/不仅如此 | 此外，还有... | 另外 / 还有 / 再加上 |
| Overuse of 的 | 这是一个非常重要的决定 | 这决定很关键 |
| Stiff conjunctions | 因此，我们可以得出结论 | 所以 / 那么 / 就是说 |
| Academic padding | 在一定程度上 | Drop or be specific |
| Double negatives | 不是不无道理 | 有道理 |
| Westernized syntax | 对于这个问题，我们有... | 这个问题，我们... |
| 综上所述/基于以上分析 | 综上所述，建议... | 总的来说 / 所以建议... |

## Rewriting Rules

1. **Shorten sentences**: Split sentences longer than 40 chars
2. **Add rhythm**: Mix long and short sentences
3. **Use colloquial transitions**: 说实话、说白了、你看、其实
4. **Drop formal padding**: 在某种程度上 → be specific or drop
5. **Use 口语化 terms**: 大家 → 咱们 / 我们, 使用 → 用, 进行 → 做/干
6. **Add personal voice**: Inject 我觉得/我认为/我的经验是 when appropriate
7. **Use Chinese idioms naturally**: 事半功倍, 一举两得 (sparingly, not forced)

## Before/After Example

**Before (AI-sounding):**
值得注意的是，黄金价格在过去一周内呈现出显著的上行走势，这主要是由于市场对美联储降息预期的增强。此外，地缘政治风险也在一定程度上支撑了金价。综上所述，建议投资者密切关注本周非农数据。

**After (humanized):**
这周黄金涨得挺猛。说白了就是市场赌美联储要降息，加上地缘政治那堆事儿也没消停。紧盯着这周的非农数据吧。

## Guidelines
- Preserve factual accuracy — never change data, numbers, or key arguments
- Match the original tone intent (professional vs casual)
- Don't over-humanize technical/legal docs — keep precision
