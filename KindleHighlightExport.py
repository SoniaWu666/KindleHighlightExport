# -*- coding: UTF-8 -*-
import os
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

def read_clippings(filename):
    with open(filename, mode='r', encoding='UTF-8') as file:
        content = file.read()
    
    # Split the content into individual clippings
    clippings = content.split('==========')
    
    # Process each clipping
    books = defaultdict(list)
    years = defaultdict(set)  # Store unique years and their associated books
    for clipping in clippings:
        lines = clipping.strip().split('\n')
        if len(lines) >= 3:
            book_title = lines[0].strip()
            metadata = lines[1].strip()
            highlight = '\n'.join(lines[2:]).strip()  # Join remaining lines as highlight content
            
            # Handle metadata line starting with '-'
            if metadata.startswith('- '):
                metadata = metadata[2:].strip()  # Remove the '- ' prefix
            
            # Extract position and date from metadata
            if ('您在第' in metadata or '您在位置' in metadata) and '添加于' in metadata:
                # Handle different position formats
                if '您在第' in metadata:
                    # Format: 您在第 2374 页（位置 #36390-36397）的标注
                    position = metadata.split('位置 #')[1].split(')')[0]
                else:
                    # Format: 您在位置 #323-325的标注
                    position = metadata.split('您在位置 #')[1].split('的标注')[0]
                
                date_str = metadata.split('添加于 ')[1].split('|')[0].strip()  # 只保留第一部分
                
                # Remove the day of the week (e.g., "星期二") from the date string
                date_str = date_str.split()[0]  # Keep only the date part (e.g., "2024年12月31日")
                
                # Extract the year from the date string
                year = date_str.split('年')[0]
                years[year].add(book_title)  # Add the book to the year's set
                
                # Convert the date string to a datetime object
                try:
                    date = datetime.strptime(date_str, "%Y年%m月%d日")
                except ValueError:
                    # If parsing fails, use the original string
                    date = date_str
                
                # Store the highlight with its metadata
                books[book_title].append({
                    'position': position,
                    'date': date_str,  # Use the original date string for display
                    'highlight': highlight,
                    'year': year  # Store the year for filtering
                })
    
    return books, years  # Return books and years with book counts

def generate_html(books, output_folder, selected_years):
    exported_count = 0  # 统计实际导出的 HTML 文件数量
    for book_title, highlights in books.items():
        # Filter highlights by selected years
        filtered_highlights = [h for h in highlights if h["year"] in selected_years]
        if not filtered_highlights:
            continue  # Skip this book if no highlights for the selected years
        
        # Get the last annotation date (without time and weekday)
        last_date = filtered_highlights[-1]["date"].split()[0]  # Use the date part only (e.g., "2024年12月31日")
        
        # Create a valid filename by removing invalid characters
        safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '.', '_')).rstrip()
        
        # Limit the length of the filename (e.g., 50 characters)
        max_filename_length = 50  # 设置文件名最大长度
        if len(safe_title) > max_filename_length:
            safe_title = safe_title[:max_filename_length]  # 截取前50个字符
        
        output_filename = os.path.join(output_folder, f"{last_date}_{safe_title}.html")
        
        with open(output_filename, mode='w', encoding='UTF-8') as file:
            file.write('''<html>
<head>
<title>My Clippings</title>
<style>
    body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        margin: 20px;
        padding: 0;
        background-color: #f9f9f9;
        color: #333;
    }
    h1 {
        color: #4CAF50;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 10px;
    }
    .metadata {
        font-size: 0.9em;
        color: #666;
        margin-bottom: 5px;
    }
    .highlight {
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid #ddd;
    }
    .highlight:last-child {
        border-bottom: none;
    }
    blockquote {
        margin: 0;
        padding: 10px;
        background: #f0f0f0;
        border-left: 3px solid #ccc;
        color: #000;
    }
</style>
</head>
<body>
''')
            file.write(f'<h1>{book_title}</h1>\n')
            for highlight in filtered_highlights:
                # 修正位置信息：去掉多余的右括号和“的标注”
                position = highlight["position"].replace('）', '').replace('的标注', '')
                
                # 修正日期信息：只保留“添加于”部分
                date_info = highlight["date"].split('|')[0].strip()  # 只保留第一部分
                
                # 写入修正后的内容
                file.write(f'''
                <div class="highlight">
                    <div class="metadata">
                        <strong>位置:</strong> {position} 
                    </div>
                    <blockquote>{highlight["highlight"]}</blockquote>
                </div>
                ''')
            file.write('</body>\n</html>\n')
        
        exported_count += 1  # 每导出一个文件，计数器加 1
    
    messagebox.showinfo("完成", f"已生成 {exported_count} 个HTML文件到 {output_folder}")

def select_input_file():
    file_path = filedialog.askopenfilename(
        title="选择 My Clippings.txt 文件",
        filetypes=[("Text Files", "*.txt")]
    )
    if file_path:
        input_file_entry.delete(0, tk.END)
        input_file_entry.insert(0, file_path)
        
        # Automatically set output folder to a new folder named "日期+导出的笔记" in the same directory
        input_folder = os.path.dirname(file_path)
        today_date = datetime.now().strftime("%Y%m%d")
        default_output_folder = os.path.join(input_folder, f"{today_date}导出的笔记")
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, default_output_folder)
        
        # Read the clippings and extract years
        global books, years, year_vars
        books, years = read_clippings(file_path)
        
        # Clear previous checkboxes
        for widget in year_frame.winfo_children():
            widget.destroy()
        
        # Create checkboxes for each year, default to all selected
        year_vars = {}  # Initialize year_vars
        for year, book_set in sorted(years.items()):
            var = tk.BooleanVar(value=True)  # Default to checked
            year_vars[year] = var
            # Display year with the number of books
            cb = tk.Checkbutton(year_frame, text=f"{year} ({len(book_set)} 本书)", variable=var)
            cb.pack(anchor=tk.W)

def select_output_folder():
    folder_path = filedialog.askdirectory(title="选择导出HTML文件的文件夹")
    if folder_path:
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, folder_path)

def start_conversion():
    input_file = input_file_entry.get()
    output_folder = output_folder_entry.get()
    
    if not input_file or not output_folder:
        messagebox.showerror("错误", "请选择输入文件和输出文件夹")
        return
    
    if not os.path.isfile(input_file):
        messagebox.showerror("错误", "输入的My Clippings.txt文件不存在")
        return
    
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Get selected years
    global year_vars
    if 'year_vars' not in globals():
        messagebox.showerror("错误", "请先选择输入文件")
        return
    
    selected_years = [year for year, var in year_vars.items() if var.get()]
    
    if not selected_years:
        messagebox.showerror("错误", "请选择至少一个年份")
        return
    
    generate_html(books, output_folder, selected_years)

# GUI setup
root = tk.Tk()
root.title("Kindle Clippings 转换工具")

# Input file selection
input_file_label = tk.Label(root, text="选择 My Clippings.txt 文件:")
input_file_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

input_file_entry = tk.Entry(root, width=50)
input_file_entry.grid(row=0, column=1, padx=5, pady=5)

input_file_button = tk.Button(root, text="浏览", command=select_input_file)
input_file_button.grid(row=0, column=2, padx=5, pady=5)

# Output folder selection
output_folder_label = tk.Label(root, text="选择导出HTML文件的文件夹:")
output_folder_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

output_folder_entry = tk.Entry(root, width=50)
output_folder_entry.grid(row=1, column=1, padx=5, pady=5)

output_folder_button = tk.Button(root, text="浏览", command=select_output_folder)
output_folder_button.grid(row=1, column=2, padx=5, pady=5)

# Year selection frame
year_frame = tk.Frame(root)
year_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

# Start conversion button
start_button = tk.Button(root, text="开始转换", command=start_conversion)
start_button.grid(row=3, column=1, padx=5, pady=10)

# Run the GUI
root.mainloop()