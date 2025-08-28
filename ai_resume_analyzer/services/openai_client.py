import os

def generate_job_fit(resume_text: str, job_title: str, job_desc: str):
    """Uses OpenAI API if available. Falls back to rule-based summary if not."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        summary = "LLM not configured. Showing quick heuristic summary based on keyword overlap."
        recs = (
            "- Highlight the most relevant experiences at the top.\n"
            "- Add measurable outcomes (metrics) to key bullets.\n"
            "- Mirror terminology from the job description to pass ATS filters."
        )
        return summary, recs

    try:
        import openai
        openai.api_key = api_key

        system = "You are a precise, helpful technical recruiter. Be concise, structured, and pragmatic."
        prompt = f"""
        Job Title: {job_title}

        Job Description:
        {job_desc}

        Resume:
        {resume_text}

        1) Give a 4-6 bullet executive summary of the candidate's fit.
        2) Provide an overall fit rating out of 10 with a one-line rationale.
        3) List the top 8-12 missing skills/keywords relative to the job.
        4) Suggest 5-7 resume improvements tailored to this job.
        """

        resp = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        text = resp.choices[0].message.content
        parts = text.split("\n\n")
        summary = parts[0].strip()
        recs = "\n".join(p.strip() for p in parts[1:]) if len(parts) > 1 else ""
        return summary, recs

    except Exception as e:
        summary = "LLM call failed. Falling back to heuristic output."
        recs = f"- Error: {e}\n- Try verifying your API key and model name."
        return summary, recs
