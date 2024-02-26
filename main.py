from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, TypeHandler

import config
import db.func as db_func
import tg.func as tg_func
from parser.post import clean_input, determine_data_type, post_request_data
from utils import get_msg


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    if db_func.get_user(user_id=user.id).count() == 0:
        msg = f"#New: {user.id}\n" + rf"{user.mention_html()}" + f"\n{tg_func.get_username(user)}" + f"\n{user.link}"
        await tg_func.send_admins(msg)

    db_func.set_user(
        user_id=user.id,
        first=user.first_name,
        last=user.last_name,
        username=user.username,
        url=user.link,
        lang_code=user.language_code,
    )

    await update.message.reply_html(
        f"{get_msg(user, 'start')}",
        # reply_markup=ForceReply(selective=True),
    )


async def set_last_touch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action_data = None
    message_id = None
    if update.message:
        action_data = update.message.text
        message_id = update.message.message_id
    elif update.callback_query:
        action_data = update.callback_query.data

    user_id = tg_func.get_user_id(update)
    if user_id:
        if action_data:
            db_func.set_last_touch(user_id)

            if action_data:
                action_data = str(action_data)

            db_func.set_user_action(user_id=user_id, message=action_data[:4000], message_id=message_id)
    else:
        tg_func.remove_jobs(name=str(user_id), context=context)
        return


@tg_func.only_admin_async
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    in_text = clean_input(update.message.text)  # Или используйте ваш regn, например, "91-17-005023"
    len_text = len(in_text)

    data_type = determine_data_type(in_text)

    if not data_type:
        await update.message.reply_text("ИНН должен быть 10 или 12 знаков")
        # , Регистрационный номер должен быть 12 знаков, включая знак тире.
        return

    if data_type == "inn" and len_text not in [10, 12]:
        await update.message.reply_text(f"ИНН должен быть 10 или 12 знаков, получено: {len_text}")
        return
    # elif data_type == "regn" and len_text != 12:
    #     await update.message.reply_text(f"Регистрационный номер должен быть 12 знаков, получено: {len_text}")
    #     return

    resp = await post_request_data(
        # regn=in_text if data_type == "regn" else None,
        inn=in_text
        if data_type == "inn"
        else None,
    )
    await update.message.reply_html(text=resp)


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(config.API_KEY).build()

    application.add_handler(TypeHandler(Update, callback=set_last_touch), group=1)
    application.add_error_handler(tg_func.error_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # application.add_handler(
    #     MessageHandler(filters.TEXT & ~filters.COMMAND & filters.REPLY, tg_func.send_msg_router, block=False)
    # )
    # application.add_handler(
    #     MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.FORWARDED, tg_func.send_msg_router, block=False)
    # )

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.FORWARDED, get_data, block=False))

    application.run_polling()


if __name__ == "__main__":
    main()
