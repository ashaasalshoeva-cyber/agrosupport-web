"""Run once on the laptop: py -3 setup_admin.py"""
import getpass
from photo_store import has_admin, set_admin_password

print('AAIAP: настройка доступа к редактору фотографий')
print('Данные будут сохранены локально в data/admin.json (только хеш пароля).')
if has_admin():
    print('ВНИМАНИЕ: пароль уже установлен; продолжение заменит его.')
    answer = input('Чтобы продолжить, напишите ДА: ').strip()
    if answer != 'ДА':
        print('Без изменений.'); raise SystemExit(0)
while True:
    password = getpass.getpass('Придумайте пароль администратора (12+ символов): ')
    if len(password) < 12:
        print('Пароль слишком короткий.'); continue
    if password != getpass.getpass('Повторите пароль: '):
        print('Пароли не совпадают.'); continue
    set_admin_password(password)
    print('Готово. Теперь запустите сервер и откройте «Редактор фото».')
    break
