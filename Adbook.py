from tkinter import *
from tkinter import messagebox
import sqlite3

win = Tk()
win.title('Address Book')
win.geometry('500x300')
win.option_add('*font', 'tahoma 10')
win.option_add('*Button*background', 'lightgray')

# ----- Frame สำหรับวาง Listbox และ Scrollbar ----------------------------
frame_listbox = Frame(win)
frame_listbox.pack(side=LEFT, padx=20, pady=20, anchor=NW)
listbox = Listbox(frame_listbox, height=15, width=22, selectmode=SINGLE, exportselection=0)
listbox.bind('<<ListboxSelect>>', lambda e: listbox_select())
listbox.grid(row=0, column=0)

scroll_y = Scrollbar(frame_listbox, orient=VERTICAL, command=listbox.yview)
scroll_y.grid(row=0, column=1, stick=N + S)
listbox.config(yscrollcommand=scroll_y.set)

# --- Frame: ข้อมูลส่วนตัว --------------------------------------------------
frame_info = LabelFrame(win, text='ข้อมูลส่วนตัว')
frame_info.pack(side=LEFT, padx=0, pady=20, anchor=NW)


# ฟังก์ชันสำหรับเพิ่มวิดเจ็ตลงในเฟรม (จัดโครงร่างแบบ grid)
def add_grid(w, r, c, cspan=1):
    w.grid(row=r, column=c, columnspan=cspan, sticky=NW, padx=10, pady=5)


add_grid(Label(frame_info, text='id:'), r=0, c=0)
entry_id = Entry(frame_info, width=14, bg='lightgray')
entry_id.bind('<Key>', lambda e: 'break')
add_grid(entry_id, r=0, c=1, cspan=2)

add_grid(Label(frame_info, text='ชื่อ:'), r=1, c=0)
entry_name = Entry(frame_info, width=24)
add_grid(entry_name, r=1, c=1, cspan=2)

add_grid(Label(frame_info, text='ที่อยู่:'), r=2, c=0)
text_address = Text(frame_info, width=24, height=3)
add_grid(text_address, r=2, c=1, cspan=2)

add_grid(Label(frame_info, text='โทร:'), r=3, c=0)
entry_phone = Entry(frame_info, width=24)
add_grid(entry_phone, r=3, c=1, cspan=2)

add_grid(Label(frame_info, text='อีเมล:'), r=4, c=0)
entry_email = Entry(frame_info, width=24)
add_grid(entry_email, r=4, c=1, cspan=2)

# นำ Entry มาสร้างเป็นลิสต์เพื่อความสะดวกต่อการเข้าถึง
entries = [entry_id, entry_name, text_address, entry_phone, entry_email]

button_add = Button(frame_info, text='เพิ่ม', command=lambda: button_add_click())
button_add.grid(row=5, column=0, padx=10, pady=10)

button_save = Button(frame_info, text='บันทึกการเพิ่ม/แก้ไข', command=lambda: button_save_click())
button_save.grid(row=5, column=1, padx=10, pady=10)

button_delete = Button(frame_info, text='ลบ', command=lambda: button_delete_click())
button_delete.grid(row=5, column=2, padx=10, pady=10)

# ----- database connection & global variables -------------------------
con = sqlite3.connect('abdb.sqlite')
cursor = con.cursor()

_data = []
_listbox_selected_index = -1


# ----- functions ------------------------------------------------
def read_database():
    global _data
    _data.clear()
    sql = 'SELECT * FROM addressbook'
    cursor.execute(sql)
    _data = cursor.fetchall()


# แสดงรายชื่อใน Listbox
def listbox_set_items():
    names = []
    listbox.delete(0, END)
    for r in _data:
        names.append(r[1])

    listbox.insert(0, *names)


# เมื่อคลิกรายการใดของ Listbox ให้นำลำดับของรายการนั้น
# ไปเป็นลำดับในการอ่านค่าจากลิสต์ของข้อมูลผลลัพธ์ที่อ่านจากตาราง
def listbox_select(e=None):
    cur_selection = listbox.curselection()
    if len(cur_selection) == 0:
        return

    index = cur_selection[0]
    row = _data[index]
    entries_clear()
    for (i, widget) in enumerate(entries):
        if isinstance(widget, Entry):
            widget.insert(0, row[i])
        elif isinstance(widget, Text):
            widget.insert(1.0, row[i])

    global _listbox_selected_index
    _listbox_selected_index = index


def button_add_click():
    entries_clear()
    entry_id.insert(0, '')
    listbox.selection_clear(0, END)


# เมื่อคลิกปุ่ม บันทึก ให้ตรวจว่าช่อง id มีข้อมูลหรือไม่
# ถ้ามีก็ให้อัปเดตข้อมูล แต่ถ้าไม่มีก็ให้เพิ่มข้อมูลใหม่
def button_save_click():
    if entry_id.get() == '':
        insert()
    else:
        update()


def button_delete_click():
    if entry_id.get() == '':
        messagebox.showerror(message='กรุณาเลือกรายการที่จะลบ')
        return

    bt = messagebox.askokcancel(message='ยืนยันการลบข้อมูล')
    if bt is False:
        return

    sql = 'DELETE FROM addressbook WHERE id = ?'
    r = cursor.execute(sql, [entry_id.get()])
    if r.rowcount == 1:
        con.commit()
        messagebox.showinfo(message='ข้อมูลถูกลบแล้ว')
        refresh()
        entries_clear()
    else:
        messagebox.showerror(message='เกิดข้อผิดพลาด ข้อมูลไม่ถูกลบ')


# อ่านข้อมูลจาก Entry ทั้งหมดมาเก็บไว้ในลิสต์
# ซึ่งสามารถนำไปกำหนดเป็นพารามิเตอร์ของ SQL ได้ทันที
def entry_values():
    values = []
    for w in entries:
        if isinstance(w, Entry):
            values.append(w.get())
        elif isinstance(w, Text):
            values.append(w.get(1.0, END))

    return values


# กรณีการเพิ่มข้อมูล
def insert():
    sql = 'INSERT INTO addressbook VALUES(null, ?, ?, ?, ?)'
    params = entry_values()
    # เราบังคับว่าต้องระบุชื่อเสมอ ดังนั้นจึงใช้ฟังก์ชัน lstrip()/rstrip()
    # เพื่อป้องกันการใส่เฉพาะช่องว่าง
    if str(params[1]).lstrip().rstrip() == '':
        messagebox.showinfo(message='กรุณาระบุชื่อ')
        return

    del params[0]  # เนื่องจากคอลัมน์ id เป็น AutoIncrement เราจึงไม่กำหนดค่าเอง

    r = cursor.execute(sql, params)
    if r.rowcount == 1:
        con.commit()
        messagebox.showinfo(message='ข้อมูลถูกบันทึกแล้ว')
        # ให้เลือกรายการที่ถูกเพิ่มเข้าไปใหม่
        global _listbox_selected_index
        _listbox_selected_index = listbox.size()
        refresh()
    else:
        messagebox.showerror(message='เกิดข้อผิดพลาด ข้อมูลไม่ถูกบันทึก')


# กรณีการอัปเดตข้อมูล
def update():
    sql = '''UPDATE addressbook SET 
                name=?, address=?, phone=?, email=?
                WHERE id=?'''

    params = entry_values()  # เนื่องจากเราจะใช้ id ในการกำหนดเงื่อนไข แต่ตำแหน่งพารามิเตอร์
    params.append(params[0])  # ของเงื่อนไขอยู่ในลำดับสุดท้าย ดังนั้นต้องเพิ่มต่อท้ายแล้วลบอันแรกทิ้ง
    del params[0]  # เพื่อให้ลำดับข้อมูลในลิสต์ตรงกับลำดับของพารามิเตอร์

    r = cursor.execute(sql, params)
    if r.rowcount == 1:
        con.commit()
        messagebox.showinfo(message='ข้อมูลถูกบันทึกแล้ว')
        refresh()
    else:
        messagebox.showerror('Error', 'เกิดข้อผิดพลาด ข้อมูลไม่ถูกบันทึก')


# หลังการเปลี่ยนแปลง จะเรียกฟังก์ชันนี้เพื่อโหลดข้อมูลจากตารางมาใหม่
def refresh():
    read_database()
    listbox_set_items()
    listbox_invoke(_listbox_selected_index)


# หลังการเพิ่มหรือลบข้อมูล จะเรียกฟังก์ชันนี้ เพื่อลบข้อความใน Entry ทุกอัน
def entries_clear():
    for w in entries:
        if isinstance(w, Entry):
            start = 0
        elif isinstance(w, Text):
            start = 1.0

        w.delete(start, END)


def listbox_invoke(index):
    listbox.selection_set(index)
    listbox_select()


# ----- เริ่มต้น ให้อ่านข้อมูลจากตาราง แล้วเลือกรายการแรกของ Listbox ----------
read_database()
listbox_set_items()
if listbox.size() > 0:
    listbox_invoke(0)

mainloop()

