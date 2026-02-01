import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from datetime import datetime


class Document:
    def __init__(self, parent_tab, filename=None):
        self.parent_tab = parent_tab
        self.filename = filename
        self.modified = False
        self.text_widget = None

    @property
    def has_name(self):
        return self.filename is not None

    @property
    def short_name(self):
        if self.has_name:
            return os.path.basename(self.filename)
        return "Без имени"

    @property
    def full_name(self):
        return self.filename if self.has_name else "Без имени"

    def open(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            self.filename = filename
            self.modified = False
            return content
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")
            return None

    def save(self, content):
        if not self.has_name:
            return False
        try:
            with open(self.filename, 'w', encoding='utf-8') as file:
                file.write(content)
            self.modified = False
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
            return False

    def save_as(self, filename, content):
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(content)
            self.filename = filename
            self.modified = False
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
            return False


class RecentList:
    def __init__(self, max_items=5):
        self.max_items = max_items
        self.items = []
        self.config_file = "recent_files.json"

    def add(self, filename):
        # Удаляем если уже есть
        if filename in self.items:
            self.items.remove(filename)

        # Добавляем в начало
        self.items.insert(0, filename)

        # Ограничиваем количество
        if len(self.items) > self.max_items:
            self.items = self.items[:self.max_items]

        self.save_data()

    def remove(self, filename):
        if filename in self.items:
            self.items.remove(filename)
            self.save_data()

    def save_data(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self.items, file)
        except:
            pass

    def load_data(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    self.items = json.load(file)

                    # Проверяем существование файлов
                    self.items = [f for f in self.items if os.path.exists(f)]
                    self.save_data()
        except:
            self.items = []


class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Текстовый редактор")
        self.root.geometry("1000x700")

        # Инициализация компонентов
        self.recent_list = RecentList()
        self.recent_list.load_data()

        self.documents = []  # Список объектов Document
        self.current_doc_index = -1

        self.setup_ui()

        # Создаем начальный документ
        self.new_doc()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def setup_ui(self):
        # Создаем меню
        self.create_menu()

        # Создаем панель вкладок
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(fill='both', expand=True)
        self.tab_control.bind('<<NotebookTabChanged>>', self.on_tab_changed)

        # Контекстное меню для вкладок
        self.tab_menu = tk.Menu(self.root, tearoff=0)
        self.tab_menu.add_command(label="Закрыть", command=self.close_current_tab)
        self.tab_menu.add_command(label="Закрыть все кроме текущей", command=self.close_other_tabs)

        self.tab_control.bind('<Button-3>', self.show_tab_menu)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)

        file_menu.add_command(label="Новый", command=self.new_doc, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть", command=self.open_doc, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_doc, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как", command=self.save_doc_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Закрыть", command=self.close_active_doc, accelerator="Ctrl+W")
        file_menu.add_separator()

        # Подменю Recent
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Недавние", menu=self.recent_menu)
        self.update_recent_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.exit_app, accelerator="Alt+F4")

        # Меню Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)

        edit_menu.add_command(label="Отменить", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Вырезать", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Копировать", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Вставить", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_command(label="Удалить", command=self.delete, accelerator="Del")
        edit_menu.add_separator()
        edit_menu.add_command(label="Выделить все", command=self.select_all, accelerator="Ctrl+A")

        # Меню Вид
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)

        self.font_size_var = tk.IntVar(value=12)
        font_sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24]
        size_menu = tk.Menu(view_menu, tearoff=0)
        for size in font_sizes:
            size_menu.add_radiobutton(label=str(size), variable=self.font_size_var,
                                      value=size, command=self.change_font_size)
        view_menu.add_cascade(label="Размер шрифта", menu=size_menu)

        # Привязка горячих клавиш
        self.root.bind_all('<Control-n>', lambda e: self.new_doc())
        self.root.bind_all('<Control-o>', lambda e: self.open_doc())
        self.root.bind_all('<Control-s>', lambda e: self.save_doc())
        self.root.bind_all('<Control-Shift-S>', lambda e: self.save_doc_as())
        self.root.bind_all('<Control-w>', lambda e: self.close_active_doc())
        self.root.bind_all('<Control-z>', lambda e: self.undo())
        self.root.bind_all('<Control-y>', lambda e: self.redo())
        self.root.bind_all('<Control-x>', lambda e: self.cut())
        self.root.bind_all('<Control-c>', lambda e: self.copy())
        self.root.bind_all('<Control-v>', lambda e: self.paste())
        self.root.bind_all('<Control-a>', lambda e: self.select_all())

    def update_recent_menu(self):
        """Обновление меню недавних файлов"""
        self.recent_menu.delete(0, 'end')

        if not self.recent_list.items:
            self.recent_menu.add_command(label="Нет недавних файлов", state='disabled')
        else:
            for i, filename in enumerate(self.recent_list.items):
                short_name = os.path.basename(filename)
                self.recent_menu.add_command(
                    label=f"{i + 1}. {short_name}",
                    command=lambda f=filename: self.open_doc_by_recent(f)
                )
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Очистить список", command=self.clear_recent_list)

    def clear_recent_list(self):
        """Очистка списка недавних файлов"""
        self.recent_list.items = []
        self.recent_list.save_data()
        self.update_recent_menu()

    def new_doc(self):
        """Создание нового документа"""
        # Создаем новую вкладку
        tab = ttk.Frame(self.tab_control)
        self.tab_control.add(tab, text="Без имени")
        self.tab_control.select(tab)

        # Создаем текстовое поле
        text_widget = tk.Text(tab, wrap='word', undo=True, font=('Arial', self.font_size_var.get()))
        text_widget.pack(fill='both', expand=True)

        # Создаем документ
        doc = Document(tab)
        doc.text_widget = text_widget
        self.documents.append(doc)
        self.current_doc_index = len(self.documents) - 1

        # Отслеживаем изменения
        text_widget.bind('<<Modified>>', self.on_text_modified)

        # Устанавливаем фокус
        text_widget.focus_set()

    def on_text_modified(self, event):
        """Обработчик изменения текста"""
        widget = event.widget
        if widget.edit_modified():
            idx = self.get_tab_index_by_widget(widget)
            if idx != -1 and idx < len(self.documents):
                self.documents[idx].modified = True
                current_text = self.tab_control.tab(self.current_tab, "text")
                if not current_text.startswith("*"):
                    self.tab_control.tab(self.current_tab, text="*" + current_text)
            widget.edit_modified(False)

    def get_tab_index_by_widget(self, widget):
        """Получить индекс вкладки по виджету"""
        for i, doc in enumerate(self.documents):
            if doc.text_widget == widget:
                return i
        return -1

    @property
    def current_tab(self):
        """Получить текущую вкладку"""
        return self.tab_control.select()

    @property
    def current_document(self):
        """Получить текущий документ"""
        if 0 <= self.current_doc_index < len(self.documents):
            return self.documents[self.current_doc_index]
        return None

    def on_tab_changed(self, event):
        """Обработчик смены вкладки"""
        selected = self.tab_control.select()
        if selected:
            # Находим индекс документа по вкладке
            for i, doc in enumerate(self.documents):
                if doc.parent_tab == self.tab_control.nametowidget(selected):
                    self.current_doc_index = i
                    break

    def open_doc(self, filename=None):
        """Открытие документа"""
        if not filename:
            filename = filedialog.askopenfilename(
                title="Открыть файл",
                filetypes=[
                    ("Текстовые файлы", "*.txt"),
                    ("Все файлы", "*.*")
                ]
            )

        if filename:
            # Проверяем, не открыт ли уже файл
            if self.doc_opened(filename):
                # Переключаемся на уже открытый документ
                for i, doc in enumerate(self.documents):
                    if doc.filename == filename:
                        self.tab_control.select(doc.parent_tab)
                        return
                return

            # Читаем содержимое файла
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")
                return

            # Создаем новую вкладку
            tab = ttk.Frame(self.tab_control)
            short_name = os.path.basename(filename)
            self.tab_control.add(tab, text=short_name)
            self.tab_control.select(tab)

            # Создаем текстовое поле
            text_widget = tk.Text(tab, wrap='word', undo=True, font=('Arial', self.font_size_var.get()))
            text_widget.pack(fill='both', expand=True)
            text_widget.insert('1.0', content)

            # Создаем документ
            doc = Document(tab, filename)
            doc.text_widget = text_widget
            doc.modified = False
            self.documents.append(doc)
            self.current_doc_index = len(self.documents) - 1

            # Отслеживаем изменения
            text_widget.bind('<<Modified>>', self.on_text_modified)

            # Добавляем в список недавних
            self.recent_list.add(filename)
            self.update_recent_menu()

            # Устанавливаем фокус
            text_widget.focus_set()

    def open_doc_by_recent(self, filename):
        """Открытие документа из списка недавних"""
        if os.path.exists(filename):
            self.open_doc(filename)
        else:
            messagebox.showwarning("Файл не найден", f"Файл {filename} не существует.")
            self.recent_list.remove(filename)
            self.update_recent_menu()

    def doc_opened(self, filename):
        """Проверка, открыт ли уже документ"""
        for doc in self.documents:
            if doc.filename == filename:
                return True
        return False

    def save_doc(self):
        """Сохранение текущего документа"""
        doc = self.current_document
        if not doc:
            return

        content = doc.text_widget.get('1.0', 'end-1c')

        if doc.has_name:
            if doc.save(content):
                # Обновляем заголовок вкладки
                self.tab_control.tab(self.current_tab, text=doc.short_name)
                return True
        else:
            return self.save_doc_as()
        return False

    def save_doc_as(self):
        """Сохранение документа с новым именем"""
        doc = self.current_document
        if not doc:
            return False

        filename = filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )

        if filename:
            content = doc.text_widget.get('1.0', 'end-1c')
            if doc.save_as(filename, content):
                # Обновляем заголовок вкладки
                self.tab_control.tab(self.current_tab, text=doc.short_name)

                # Добавляем в список недавних
                self.recent_list.add(filename)
                self.update_recent_menu()
                return True

        return False

    def close_active_doc(self):
        """Закрытие активного документа"""
        if not self.documents:
            return

        doc = self.current_document
        if not doc:
            return

        self.close_tab(self.current_doc_index)

    def close_tab(self, index):
        """Закрытие вкладки по индексу"""
        if 0 <= index < len(self.documents):
            doc = self.documents[index]

            # Проверяем необходимость сохранения
            if doc.modified:
                response = messagebox.askyesnocancel(
                    "Сохранение документа",
                    f"Сохранить изменения в документе '{doc.short_name}'?"
                )

                if response is None:  # Cancel
                    return
                elif response:  # Yes
                    if not self.save_doc():
                        return  # Не закрываем если сохранение отменено

            # Удаляем вкладку
            self.tab_control.forget(doc.parent_tab)
            self.documents.pop(index)

            # Обновляем текущий индекс
            if self.documents:
                self.current_doc_index = min(index, len(self.documents) - 1)
            else:
                self.current_doc_index = -1
                # Создаем пустой документ если закрыли все
                self.new_doc()

    def close_current_tab(self):
        """Закрытие текущей вкладки (из контекстного меню)"""
        if self.documents:
            # Получаем индекс по позиции мыши
            tab_id = self.tab_control.select()
            if tab_id:
                tab_index = self.tab_control.index(tab_id)
                self.close_tab(tab_index)

    def close_other_tabs(self):
        """Закрытие всех вкладок кроме текущей"""
        if len(self.documents) <= 1:
            return

        current_index = self.current_doc_index
        # Закрываем с конца чтобы индексы не сбивались
        for i in range(len(self.documents) - 1, -1, -1):
            if i != current_index:
                self.close_tab(i)

    def show_tab_menu(self, event):
        """Показать контекстное меню для вкладки"""
        try:
            # Определяем на какой вкладке было нажатие
            tab_id = self.tab_control.tk.call(self.tab_control._w, "identify", "tab", event.x, event.y)
            if tab_id:
                self.tab_control.select(tab_id)
                self.tab_menu.post(event.x_root, event.y_root)
        except:
            pass

    def exit_app(self):
        """Выход из приложения"""
        # Проверяем все документы на необходимость сохранения
        unsaved = False
        for i, doc in enumerate(self.documents):
            if doc.modified:
                unsaved = True
                # Переключаемся на несохраненную вкладку
                self.tab_control.select(doc.parent_tab)

                response = messagebox.askyesnocancel(
                    "Сохранение документа",
                    f"Сохранить изменения в документе '{doc.short_name}'?"
                )

                if response is None:  # Cancel
                    return
                elif response:  # Yes
                    if not self.save_doc():
                        return  # Не выходим если сохранение отменено

        # Сохраняем список недавних файлов
        self.recent_list.save_data()

        # Закрываем приложение
        self.root.quit()

    # Методы для меню Правка
    def undo(self):
        doc = self.current_document
        if doc and doc.text_widget:
            try:
                doc.text_widget.event_generate("<<Undo>>")
            except:
                pass

    def redo(self):
        doc = self.current_document
        if doc and doc.text_widget:
            try:
                doc.text_widget.event_generate("<<Redo>>")
            except:
                pass

    def cut(self):
        doc = self.current_document
        if doc and doc.text_widget:
            doc.text_widget.event_generate("<<Cut>>")

    def copy(self):
        doc = self.current_document
        if doc and doc.text_widget:
            doc.text_widget.event_generate("<<Copy>>")

    def paste(self):
        doc = self.current_document
        if doc and doc.text_widget:
            doc.text_widget.event_generate("<<Paste>>")

    def delete(self):
        doc = self.current_document
        if doc and doc.text_widget:
            doc.text_widget.delete("sel.first", "sel.last")

    def select_all(self):
        doc = self.current_document
        if doc and doc.text_widget:
            doc.text_widget.tag_add("sel", "1.0", "end")
            doc.text_widget.mark_set("insert", "1.0")
            doc.text_widget.see("1.0")

    def change_font_size(self):
        """Изменение размера шрифта"""
        size = self.font_size_var.get()
        for doc in self.documents:
            if doc.text_widget:
                doc.text_widget.config(font=('Arial', size))


def main():
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()