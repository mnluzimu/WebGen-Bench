appearance_prompt = """
Instruction:
You are tasked with evaluating the functional design of a webpage that had been constructed based on the following instruction:

{instruction}

Grade the webpage’s appearance on a scale of 1 to 5 (5 being highest), considering the following criteria:

  - Successful Rendering: Does the webpage render correctly without visual errors? Are colors, fonts, and components displayed as specified?
  - Content Relevance: Does the design align with the website’s purpose and user requirements? Are elements (e.g., search bars, report formats) logically placed and functional?
  - Layout Harmony: Is the arrangement of components (text, images, buttons) balanced, intuitive, and clutter-free?
  - Modernness & Beauty: Does the design follow contemporary trends (e.g., minimalism, responsive layouts)? Are colors, typography, and visual hierarchy aesthetically pleasing?

Grading Scale:

  - 1 (Poor): Major rendering issues (e.g., broken layouts, incorrect colors). Content is irrelevant or missing. Layout is chaotic. Design is outdated or visually unappealing.
  - 2 (Below Average): Partial rendering with noticeable errors. Content is partially relevant but poorly organized. Layout lacks consistency. Design is basic or uninspired.
  - 3 (Average): Mostly rendered correctly with minor flaws. Content is relevant but lacks polish. Layout is functional but unremarkable. Design is clean but lacks modern flair.
  - 4 (Good): Rendered well with no major errors. Content is relevant and logically organized. Layout is harmonious and user-friendly. Design is modern and visually appealing.
  - 5 (Excellent): Flawless rendering. Content is highly relevant, intuitive, and tailored to user needs. Layout is polished, responsive, and innovative. Design is cutting-edge, beautiful, and memorable.

Task:
Review the provided screenshot(s) of the webpage. Provide a detailed analysis and then assign a grade (1–5) based on your analysis. Highlight strengths, weaknesses, and how well the design adheres to the specifications.

Your Response Format:

Analysis: [2–4 paragraphs addressing all criteria, referencing the instruction]

Grade: [1–5]

Your Response:
"""