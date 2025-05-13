from telegram import Update
from telegram.ext import ContextTypes
from app.modules.ai.gemini import AIService
from app.modules.system.service import CommandService

class CommandHandlers:
    def __init__(self):
        self.ai = AIService()
        self.cmd_service = CommandService()

    async def handle_text_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_text = update.message.text
        try:
            # Преобразование через ИИ
            system_cmd = self.ai.parse_command(user_text)
            
            # Выполнение команды
            result = self.cmd_service.execute(system_cmd)
            
            await update.message.reply_text(
                f"✅ Выполнено:\n{system_cmd}\n\n"
                f"Результат:\n{result['output'][:1000]}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")