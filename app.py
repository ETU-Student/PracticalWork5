import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
from tkinter import messagebox
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from jinja2 import Template
import threading
import time


class AppException(Exception):
    def __init__(self, message='Произошла ошибка в приложении'):
        super().__init__(message)

    @classmethod
    def validation_error(cls, message='Ошибка: все поля должны быть заполнены!'):
        return cls(message=message)

class Person:
    def __init__(self, first_name, last_name, patronymic):
        self._first_name = first_name
        self._last_name = last_name
        self._patronymic = patronymic

    def get_first_name(self):
        return self._first_name

    def get_last_name(self):
        return self._last_name

    def get_patronymic(self):
        return self._patronymic

    def get_full_name(self):
        return f"{self._last_name} {self._first_name} {self._patronymic}"

    def set_first_name(self, first_name):
        self._first_name = first_name

    def set_last_name(self, last_name):
        self._last_name = last_name

    def set_patronymic(self, patronymic):
        self._patronymic = patronymic

class Student(Person):
    def __init__(self, first_name, last_name, patronymic, group, status):
        super().__init__(first_name, last_name, patronymic)
        self._group = group
        self._status = status

    def get_group(self):
        return self._group

    def get_status(self):
        return self._status

    def set_group(self, group):
        self._group = group

    def set_status(self, status):
        self._status = status

class Teacher(Person):
    def __init__(self, first_name, last_name, patronymic, subject):
        super().__init__(first_name, last_name, patronymic)
        self._subject = subject
        self._groups = []

    def get_subject(self):
        return self._subject

    def get_groups(self):
        return self._groups

    def set_subject(self, subject):
        self._subject = subject

    def add_group(self, group):
        if group not in self._groups:
            self._groups.append(group)

    def remove_group(self, group):
        if group in self._groups:
            self._groups.remove(group)

class Group:
    def __init__(self, code):
        self._code = code
        self._students = []
        self._teachers = []

    def get_code(self):
        return self._code

    def get_students(self):
        return self._students

    def get_teachers(self):
        return self._teachers

    def add_student(self, student):
        if student not in self._students:
            self._students.append(student)

    def remove_student(self, student):
        if student in self._students:
            self._students.remove(student)

    def add_teacher(self, teacher):
        if teacher not in self._teachers:
            self._teachers.append(teacher)

    def remove_teacher(self, teacher):
        if teacher in self._teachers:
            self._teachers.remove(teacher)

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title('iZavuch')
        self.root.geometry('400x300')
        self.root.attributes('-fullscreen', True)

        self.label = tk.Label(self.root, text='Главное меню', font=('Arial', 16))
        self.label.pack(pady=10)

        self.create_comboboxes()

        self.add_report_button()  # Добавлена кнопка для создания отчётов
        self.add_multithread_button()  # Добавлена кнопка для многопоточной задачи

    def create_comboboxes(self):
        student_options = ["Список студентов", "Добавление", "Изменение", "Удаление"]
        self.student_combobox = self.create_combobox('Студенты', student_options,
                                                     command=self.on_student_option_selected)

    def create_combobox(self, label_text, options, command=None):
        label = tk.Label(self.root, text=label_text)
        label.pack(pady=5)

        combobox = ttk.Combobox(self.root, values=options)
        combobox.set("Выберите действие")
        combobox.pack(pady=5)

        if command:
            combobox.bind('<<ComboboxSelected>>', command)

        return combobox

    def on_student_option_selected(self, event):
        if self.student_combobox.get() == 'Список студентов':
            self.show_student_list()
        elif self.student_combobox.get() == 'Добавление':
            self.show_add_student_frame()
        elif self.student_combobox.get() == 'Изменение':
            self.show_edit_student_frame()
        elif self.student_combobox.get() == 'Удаление':
            self.show_delete_student_frame()

    def show_student_list(self):
        if hasattr(self, 'frame'):
            self.frame.destroy()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("ФИО", "Класс", "Статус")
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)

        students = self.load_students_from_xml('students.xml')
        for student in students:
            self.tree.insert('', tk.END, values=(student.get_full_name(), student.get_group(), student.get_status()))

        self.tree.pack(fill=tk.BOTH, expand=True)

    def show_add_student_frame(self):
        if hasattr(self, 'frame'):
            self.frame.destroy()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(self.frame, text='Имя').pack()
        self.first_name_entry = tk.Entry(self.frame)
        self.first_name_entry.pack()

        tk.Label(self.frame, text='Фамилия').pack()
        self.last_name_entry = tk.Entry(self.frame)
        self.last_name_entry.pack()

        tk.Label(self.frame, text="Отчество").pack()
        self.patronymic_entry = tk.Entry(self.frame)
        self.patronymic_entry.pack()

        tk.Label(self.frame, text="Класс").pack()
        self.group_entry = tk.Entry(self.frame)
        self.group_entry.pack()

        tk.Label(self.frame, text="Статус").pack()
        self.status_entry = tk.Entry(self.frame)
        self.status_entry.pack()

        self.save_button = tk.Button(self.frame, text='Сохранить', command=self.save_student)
        self.save_button.pack(pady=10)

    def save_student(self):
        try:
            last_name = self.last_name_entry.get()
            first_name = self.first_name_entry.get()
            patronymic = self.patronymic_entry.get()
            group = self.group_entry.get()
            status = self.status_entry.get()

            if not all([last_name, first_name, patronymic, group, status]):
                raise AppException.validation_error("Все поля должны быть заполнены для сохранения студента!")

            # Код сохранения студента в XML
            tree = ET.parse('students.xml')
            root = tree.getroot()

            new_student = ET.Element("student")
            ET.SubElement(new_student, "last_name").text = last_name
            ET.SubElement(new_student, "first_name").text = first_name
            ET.SubElement(new_student, "patronymic").text = patronymic
            ET.SubElement(new_student, "group").text = group
            ET.SubElement(new_student, "status").text = status

            root.append(new_student)
            tree.write('students.xml')

            messagebox.showinfo("Успех", "Студент успешно добавлен!")

        except AppException as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неожиданная ошибка: {str(e)}")


    def show_student_list(self):
        if hasattr(self, 'frame'):
            self.frame.destroy()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("ФИО", "Класс", "Статус")
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)

        students = self.load_students_from_xml('students.xml')
        for student in students:
            self.tree.insert('', tk.END, values=(student.get_full_name(), student.get_group(), student.get_status()))

        self.tree.pack(fill=tk.BOTH, expand=True)

    def show_add_student_frame(self):
        if hasattr(self, 'frame'):
            self.frame.destroy()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(self.frame, text='Имя').pack()
        self.first_name_entry = tk.Entry(self.frame)
        self.first_name_entry.pack()

        tk.Label(self.frame, text='Фамилия').pack()
        self.last_name_entry = tk.Entry(self.frame)
        self.last_name_entry.pack()

        tk.Label(self.frame, text="Отчество").pack()
        self.patronymic_entry = tk.Entry(self.frame)
        self.patronymic_entry.pack()

        tk.Label(self.frame, text="Класс").pack()
        self.group_entry = tk.Entry(self.frame)
        self.group_entry.pack()

        tk.Label(self.frame, text="Статус").pack()
        self.status_entry = tk.Entry(self.frame)
        self.status_entry.pack()

        self.save_button = tk.Button(self.frame, text='Сохранить', command=self.save_student)
        self.save_button.pack(pady=10)

    def save_student(self):
        if not os.path.exists('students.xml'):
            root = ET.Element("students")
            tree = ET.ElementTree(root)
            tree.write('students.xml')

        tree = ET.parse('students.xml')
        root = tree.getroot()

        last_name = self.last_name_entry.get()
        first_name = self.first_name_entry.get()
        patronymic = self.patronymic_entry.get()
        group = self.group_entry.get()
        status = self.status_entry.get()

        new_student = ET.Element("student")
        ET.SubElement(new_student, "last_name").text = last_name
        ET.SubElement(new_student, "first_name").text = first_name
        ET.SubElement(new_student, "patronymic").text = patronymic
        ET.SubElement(new_student, "group").text = group
        ET.SubElement(new_student, "status").text = status

        root.append(new_student)
        tree.write('students.xml')

        messagebox.showinfo("Успех", "Студент успешно добавлен!")

        self.first_name_entry.delete(0, tk.END)
        self.last_name_entry.delete(0, tk.END)
        self.patronymic_entry.delete(0, tk.END)
        self.group_entry.delete(0, tk.END)
        self.status_entry.delete(0, tk.END)

    def show_edit_student_frame(self):
        if hasattr(self, 'frame'):
            self.frame.destroy()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("ФИО", "Класс", "Статус")
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)

        students = self.load_students_from_xml('students.xml')
        self.student_data = []

        for idx, student in enumerate(students):
            self.tree.insert('', tk.END, values=(student.get_full_name(), student.get_group(), student.get_status()))
            self.student_data.append(student)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.select_button = tk.Button(self.frame, text="Выбрать для редактирования", command=self.edit_student)
        self.select_button.pack(pady=10)

    def edit_student(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите студента для редактирования")
            return

        item_index = self.tree.index(selected_item[0])
        self.selected_student = self.student_data[item_index]

        if hasattr(self, 'frame'):
            self.frame.destroy()

        self.show_add_student_frame()

        self.first_name_entry.insert(0, self.selected_student.get_first_name())
        self.last_name_entry.insert(0, self.selected_student.get_last_name())
        self.patronymic_entry.insert(0, self.selected_student.get_patronymic())
        self.group_entry.insert(0, self.selected_student.get_group())
        self.status_entry.insert(0, self.selected_student.get_status())

    def show_delete_student_frame(self):
        if hasattr(self, 'frame'):
            self.frame.destroy()

        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("ФИО", "Класс", "Статус")
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)

        students = self.load_students_from_xml('students.xml')
        self.student_data = []

        for idx, student in enumerate(students):
            self.tree.insert('', tk.END, values=(student.get_full_name(), student.get_group(), student.get_status()))
            self.student_data.append(student)

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.delete_button = tk.Button(self.frame, text="Удалить студента", command=self.delete_student)
        self.delete_button.pack(pady=10)

    def delete_student(self):
        try:
            selected_item = self.tree.selection()
            if not selected_item:
                raise AppException("Не выбран студент для удаления")

            item_index = self.tree.index(selected_item[0])
            student_to_delete = self.student_data[item_index]

            self.student_data.pop(item_index)
            self.tree.delete(selected_item[0])

            tree = ET.parse('students.xml')
            root = tree.getroot()

            for student_elem in root.findall("student"):
                if (student_elem.find("first_name").text == student_to_delete.get_first_name() and
                        student_elem.find("last_name").text == student_to_delete.get_last_name() and
                        student_elem.find("patronymic").text == student_to_delete.get_patronymic()):
                    root.remove(student_elem)
                    break

            tree.write('students.xml')
            messagebox.showinfo("Успех", "Студент успешно удалён")

        except AppException as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неожиданная ошибка: {str(e)}")

    def generate_reports(self):
        students = self.load_students_from_xml('students.xml')

        self.generate_pdf_report(students, "students_report.pdf")
        self.generate_html_report(students, "students_template.html", "students_report.html")

        messagebox.showinfo("Успех", "Отчеты успешно созданы!")

    def generate_pdf_report(self, students, output_file):
        pdf = canvas.Canvas(output_file, pagesize=letter)
        pdf.setFont("Helvetica", 12)

        pdf.drawString(100, 750, "Отчет о студентах")
        pdf.drawString(100, 730, "ФИО | Класс | Статус")

        y = 710
        for student in students:
            pdf.drawString(
                100, y,
                f"{student.get_full_name()} | {student.get_group()} | {student.get_status()}"
            )
            y -= 20

        pdf.save()

    def generate_html_report(self, students, template_file, output_file):
        if not os.path.exists(template_file):
            with open(template_file, 'w') as file:
                file.write("""
                <html>
                    <head><title>Отчет о студентах</title></head>
                    <body>
                        <h1>Отчет о студентах</h1>
                        <table border="1">
                            <thead>
                                <tr>
                                    <th>ФИО</th>
                                    <th>Класс</th>
                                    <th>Статус</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for student in data %}
                                <tr>
                                    <td>{{ student.full_name }}</td>
                                    <td>{{ student.group }}</td>
                                    <td>{{ student.status }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </body>
                </html>
                """)

        with open(template_file, 'r') as file:
            template = Template(file.read())

        rendered_html = template.render(data=[
            {
                'full_name': student.get_full_name(),
                'group': student.get_group(),
                'status': student.get_status()
            } for student in students
        ])

        with open(output_file, 'w') as file:
            file.write(rendered_html)

    def execute_multithread_task(self):
        # Создаем потоки
        load_thread = threading.Thread(target=self.load_data)
        edit_thread = threading.Thread(target=self.edit_data)
        report_thread = threading.Thread(target=self.generate_report)

        # Запускаем потоки
        load_thread.start()
        load_thread.join()  # Ожидание завершения потока загрузки данных

        edit_thread.start()
        edit_thread.join()  # Ожидание завершения потока редактирования данных

        report_thread.start()
        report_thread.join()  # Ожидание завершения потока генерации отчета

        print("Все задачи выполнены")

        print("Все задачи выполнены")

    def load_data(self):
        print("Загрузка данных началась...")
        if not os.path.exists('students.xml'):
            print("Файл students.xml не найден. Создание тестового файла...")
            root = ET.Element("students")
            tree = ET.ElementTree(root)
            tree.write('students.xml')
        else:
            print("Файл students.xml успешно загружен")
        print("Данные успешно загружены")

    def edit_data(self):
        print("Редактирование данных началось...")
        tree = ET.parse('students.xml')
        root = tree.getroot()

        # Добавление тестовой записи для демонстрации редактирования
        new_student = ET.Element("student")
        ET.SubElement(new_student, "first_name").text = "Иван"
        ET.SubElement(new_student, "last_name").text = "Иванов"
        ET.SubElement(new_student, "patronymic").text = "Иванович"
        ET.SubElement(new_student, "group").text = "101"
        ET.SubElement(new_student, "status").text = "Активный"

        root.append(new_student)
        tree.write('students.xml')
        print("Данные успешно отредактированы")

    def generate_report(self):
        print("Генерация отчета началась...")
        tree = ET.parse('students.xml')
        root = tree.getroot()

        students = []
        for student_elem in root.findall("student"):
            students.append({
                "first_name": student_elem.find("first_name").text,
                "last_name": student_elem.find("last_name").text,
                "patronymic": student_elem.find("patronymic").text,
                "group": student_elem.find("group").text,
                "status": student_elem.find("status").text
            })

        # Генерация PDF-отчета
        pdf = canvas.Canvas("students_report.pdf", pagesize=letter)
        pdf.setFont("Helvetica", 12)
        pdf.drawString(100, 750, "Отчет о студентах")
        y = 730
        for student in students:
            pdf.drawString(100, y, f"{student['last_name']} {student['first_name']} {student['patronymic']} | {student['group']} | {student['status']}")
            y -= 20
        pdf.save()

        # Генерация HTML-отчета
        template = Template("""
        <html>
            <head><title>Отчет о студентах</title></head>
            <body>
                <h1>Отчет о студентах</h1>
                <table border="1">
                    <thead>
                        <tr>
                            <th>ФИО</th>
                            <th>Класс</th>
                            <th>Статус</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for student in students %}
                        <tr>
                            <td>{{ student.last_name }} {{ student.first_name }} {{ student.patronymic }}</td>
                            <td>{{ student.group }}</td>
                            <td>{{ student.status }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </body>
        </html>
        """)

        rendered_html = template.render(students=students)
        with open("students_report.html", "w") as file:
            file.write(rendered_html)

        print("Отчет успешно сгенерирован")

    def add_report_button(self):
        report_button = tk.Button(self.root, text="Создать отчеты", command=self.generate_reports)
        report_button.pack(side=tk.BOTTOM, pady=10)

    def add_multithread_button(self):
        multithread_button = tk.Button(self.root, text="Выполнить многопоточную задачу",
                                       command=self.execute_multithread_task)
        multithread_button.pack(side=tk.BOTTOM, pady=10)

    def load_students_from_xml(self, filename):
        """Загружает список студентов из XML-файла."""
        students = []
        if not os.path.exists(filename):
            return students

        tree = ET.parse(filename)
        root = tree.getroot()

        for student_elem in root.findall("student"):
            first_name = student_elem.find('first_name').text
            last_name = student_elem.find('last_name').text
            patronymic = student_elem.find('patronymic').text
            group = student_elem.find('group').text
            status = student_elem.find('status').text

            student = Student(first_name, last_name, patronymic, group, status)
            students.append(student)

        return students


def main():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
