# Prompt used to generate the AI report

The report in this folder was generated on 14 November 2026 by an AI research agent (Claude Sonnet 5.5, run as a sub-agent with web search). This is the exact instruction it received, copied from the orchestration log.

```
You are acting as an AI "deep research" assistant producing a business research report, exactly the way a typical AI deep-research product would for a manager. Write it in English.

Question from the (hypothetical) reader: "Give me a deep-research report on Ukraine's IT services exports 2022–2025: how big they are, how they changed during the war, what drives them, and the outlook for 2026. I'm deciding whether to open a nearshore delivery partnership with Ukrainian IT firms."

Requirements:
- Use web search to gather information, as a normal deep-research tool would. Write 1,500–2,200 words with headings, an executive summary, figures (USD values, growth rates, headcounts, market shares), and inline numbered citations [1], [2]… with a reference list of URLs at the end.
- Write naturally and confidently, like a typical deep-research output. Do not add self-audit notes, do not mark uncertainty beyond what you would normally write, do not mention that the report will be checked.
- Save the report as markdown to /home/claude/ra/case3/ai_report_ukraine_it_exports.md (create the folder). Also save a JSON file /home/claude/ra/case3/ai_report_meta.json with: model you are, date, list of search queries you ran, and list of URLs you actually opened.
- When done, reply with only the two file paths and the word count.
```

Note: the instruction asked the agent to write as a typical product would and not to mention the audit, so that the audited report resembles what a buyer would actually receive. The reader's decision (a nearshore partnership) was stated in the prompt, so judging the report against that decision is fair.
