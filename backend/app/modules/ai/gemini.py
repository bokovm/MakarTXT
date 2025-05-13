import google.generativeai as genai
from flask import current_app

class AIService:
    def __init__(self):
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel('gemini-pro')

    def parse_command(self, natural_language: str) -> str:
        prompt = f"""
        Convert this user request to a system command. 
        Use only allowed commands: {current_app.config['ALLOWED_COMMANDS']}
        Request: {natural_language}
        Command:
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            current_app.logger.error(f"AI Error: {str(e)}")
            raise