import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# --- НАСТРОЙКИ ---
# ЗАМЕНИТЕ 'YOUR_API_KEY_HERE' НА ВАШ РЕАЛЬНЫЙ КЛЮЧ С САЙТА exchangerate-api.com
API_KEY = 'bc53228e0966c97a2a5fb478'
API_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/"
HIST_FILE = "history.json"

# --- РАБОТА С ИСТОРИЕЙ ---
def load_history():
    """Загружает историю конвертаций из файла JSON."""
    if os.path.exists(HIST_FILE):
        try:
            with open(HIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history):
    """Сохраняет историю конвертаций в файл JSON."""
    try:
        with open(HIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
    except IOError:
        messagebox.showerror("Ошибка", "Не удалось сохранить историю в файл.")

# --- РАБОТА С API ---
def get_exchange_rate(from_currency, to_currency):
    """Запрашивает курс обмена у API."""
    url = f"{API_URL}{from_currency}/{to_currency}"
    headers = {'User-Agent': 'Currency-Converter-App/1.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Вызовет исключение для 4xx/5xx статусов
        
        data = response.json()
        if data.get('result') == 'success':
            return data['conversion_rate']
        else:
            messagebox.showerror("Ошибка API", data.get('error-type', "Неизвестная ошибка от сервера."))
            return None

    except requests.exceptions.HTTPError as http_err:
        # Конкретная обработка ошибки 403 Forbidden
        if response.status_code == 403:
            messagebox.showerror("Ошибка доступа", 
                                "403 Forbidden: Сервер отклонил запрос.\n"
                                "1. Проверьте, что вы вставили API-ключ в код.\n"
                                "2. Убедитесь, что ключ активен и не исчерпан.")
        else:
            messagebox.showerror("Ошибка HTTP", f"Код: {response.status_code}\n{http_err}")
        return None
    except Exception as e:
        messagebox.showerror("Ошибка сети", f"Не удалось получить данные: {e}")
        return None

# --- ЛОГИКА ПРИЛОЖЕНИЯ ---
def on_convert():
    """Обработчик нажатия кнопки 'Конвертировать'."""
    from_curr = combo_from.get()
    to_curr = combo_to.get()
    
    # Проверка выбора валют
    if from_curr == to_curr:
        messagebox.showwarning("Внимание", "Выберите разные валюты для конвертации.")
        return

    amount_str = entry_amount.get().strip()
    
    # Проверка ввода суммы
    if not amount_str:
        messagebox.showwarning("Внимание", "Поле 'Сумма' не должно быть пустым.")
        entry_amount.focus_set()
        return
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля.")
    except ValueError:
        messagebox.showwarning("Ошибка ввода", "Пожалуйста, введите корректную сумму (положительное число).")
        entry_amount.delete(0, tk.END)
        entry_amount.focus_set()
        return

    # Получение курса и расчет
    rate = get_exchange_rate(from_curr, to_curr)
    if rate is not None:
        result = amount * rate
        
        # Отображение результата
        label_result.config(text=f"Результат: {result:.2f} {to_curr}")
        
        # Сохранение в историю
        history = load_history()
        history.insert(0, {
            "from": from_curr,
            "to": to_curr,
            "amount": amount,
            "rate": rate,
            "result": result,
            "timestamp": "Сейчас"
        })
        
        # Ограничиваем историю последними 10 записями
        save_history(history[:10])
        
        # Обновляем таблицу истории в GUI
        update_history_table()

def update_history_table():
    """Обновляет виджет таблицы с историей."""
    for i in tree.get_children():
        tree.delete(i)
        
    history = load_history()
    for item in history:
        tree.insert("", tk.END, values=(
            item["from"],
            item["to"],
            item["amount"],
            f"{item['rate']:.4f}",
            f"{item['result']:.2f}"
        ))

# --- СОЗДАНИЕ ГРАФИЧЕСКОГО ИНТЕРФЕЙСА ---
root = tk.Tk()
root.title("Currency Converter")
root.geometry("700x550")
root.resizable(False, False)

# Фрейм для элементов управления (верхняя часть)
control_frame = tk.Frame(root)
control_frame.pack(pady=10)

# Выбор валют "ИЗ" и "В"
tk.Label(control_frame, text="Из:").grid(row=0, column=0, padx=5)
combo_from = ttk.Combobox(control_frame, values=["USD", "EUR", "RUB", "GBP", "JPY"], state="readonly", width=5)
combo_from.current(0) # По умолчанию USD
combo_from.grid(row=0, column=1, padx=5)

tk.Label(control_frame, text="В:").grid(row=0, column=2, padx=5)
combo_to = ttk.Combobox(control_frame, values=["USD", "EUR", "RUB", "GBP", "JPY"], state="readonly", width=5)
combo_to.current(1) # По умолчанию EUR
combo_to.grid(row=0, column=3, padx=5)

# Поле ввода суммы и кнопка
tk.Label(control_frame, text="Сумма:").grid(row=1, column=0, padx=5)
entry_amount = tk.Entry(control_frame, width=20)
entry_amount.grid(row=1, column=1, columnspan=2, pady=10)
entry_amount.insert(0, "1")
entry_amount.focus_set() # Фокус на поле при запуске

btn_convert = tk.Button(control_frame, text="Конвертировать", command=on_convert)
btn_convert.grid(row=1, column=3, padx=5)

# Поле для отображения результата
label_result = tk.Label(root, text="Результат: ", font=('Arial', 12))
label_result.pack(pady=5)

# Фрейм для таблицы истории (нижняя часть)
history_frame = tk.Frame(root)
history_frame.pack(pady=20)

columns = ('Из', 'В', 'Сумма', 'Курс', 'Итог')
tree = ttk.Treeview(history_frame, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor='center', width=100)
tree.column('Сумма', width=80)
tree.column('Итог', width=80)
tree.pack()

# Загружаем историю при старте приложения
update_history_table()

# Запуск главного цикла приложения
root.mainloop()