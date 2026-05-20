import tkinter as tk
from tkinter import ttk
import random
import math
import time

# --- Yapılandırma ---
NODE_COUNT = 12
INITIAL_ENERGY = 100.0
GRID_SIZE = 600
BASE_STATION = (50, 50)

class SensorNode:
    def __init__(self, node_id, canvas_width, canvas_height):
        self.id = node_id
        # Sensörleri rastgele dağıt (Merkez istasyondan biraz uzağa)
        self.x = random.randint(150, canvas_width - 50)
        self.y = random.randint(150, canvas_height - 50)
        self.energy = INITIAL_ENERGY
        self.flow_rate = 1.0 + random.random() * 0.5
        self.pollution = 0.02
        self.is_active = True
        self.status = "AKTİF"
        self.packets = 0
        self.healing_mode = False
        
        # Grafik objeleri için referanslar
        self.dot = None
        self.line = None
        self.label = None
        self.energy_bar = None

    def calculate_distance(self, target_x, target_y):
        return math.sqrt((self.x - target_x)**2 + (self.y - target_y)**2)

class WSNSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("WSN Su Altyapısı - Görsel Kontrol Paneli v3.7")
        self.root.geometry("1100x700")
        self.root.configure(bg="#0f172a")

        self.nodes = []
        self.leak_target = None
        self.is_paused = False
        self.time_step = 0

        self.setup_ui()
        self.initialize_nodes()
        self.update_simulation()

    def setup_ui(self):
        # Sol Panel: Simülasyon Haritası
        self.canvas_frame = tk.Frame(self.root, bg="#1e293b", bd=2, relief="flat")
        self.canvas_frame.place(x=20, y=20, width=650, height=660)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#020617", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Grid çizgileri
        for i in range(0, 650, 50):
            self.canvas.create_line(i, 0, i, 660, fill="#1e293b")
            self.canvas.create_line(0, i, 650, i, fill="#1e293b")

        # Sağ Panel: Bilgiler
        self.info_frame = tk.Frame(self.root, bg="#0f172a")
        self.info_frame.place(x=690, y=20, width=390, height=660)

        # Başlık ve İstatistikler
        self.title_label = tk.Label(self.info_frame, text="WSN KONTROL MERKEZİ", font=("Arial", 16, "bold"), fg="#3b82f6", bg="#0f172a")
        self.title_label.pack(pady=10)

        self.stat_label = tk.Label(self.info_frame, text="Süre: 0s | Aktif Sensör: 12/12", font=("Courier", 10), fg="#94a3b8", bg="#0f172a")
        self.stat_label.pack()

        # Sensör Detay Listesi (Scrollable)
        self.list_canvas = tk.Canvas(self.info_frame, bg="#0f172a", highlightthickness=0)
        self.list_frame = tk.Frame(self.list_canvas, bg="#0f172a")
        self.scrollbar = ttk.Scrollbar(self.info_frame, orient="vertical", command=self.list_canvas.yview)
        
        self.list_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.list_canvas.pack(side="left", fill="both", expand=True, pady=10)
        self.list_canvas.create_window((0,0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")))

        # Kontrol Butonları
        self.btn_frame = tk.Frame(self.info_frame, bg="#0f172a")
        self.btn_frame.pack(side="bottom", fill="x", pady=20)

        self.pause_btn = tk.Button(self.btn_frame, text="DURDUR", command=self.toggle_pause, bg="#1e293b", fg="white", font=("Arial", 9, "bold"), relief="flat", padx=20, pady=10)
        self.pause_btn.pack(side="left", expand=True, padx=5)

        self.leak_btn = tk.Button(self.btn_frame, text="SIZINTI YAP", command=self.trigger_leak, bg="#ef4444", fg="white", font=("Arial", 9, "bold"), relief="flat", padx=20, pady=10)
        self.leak_btn.pack(side="right", expand=True, padx=5)

    def initialize_nodes(self):
        # Merkez İstasyon Çizimi
        self.canvas.create_oval(BASE_STATION[0]-15, BASE_STATION[1]-15, BASE_STATION[0]+15, BASE_STATION[1]+15, fill="#3b82f6", outline="#60a5fa", width=2)
        self.canvas.create_text(BASE_STATION[0], BASE_STATION[1]+25, text="MERKEZ", fill="#60a5fa", font=("Arial", 8, "bold"))

        for i in range(NODE_COUNT):
            node = SensorNode(i+1, 600, 600)
            
            # Haritadaki bağlantı çizgisi
            node.line = self.canvas.create_line(node.x, node.y, BASE_STATION[0], BASE_STATION[1], fill="#1e293b", dash=(4, 4))
            
            # Haritadaki sensör noktası
            node.dot = self.canvas.create_oval(node.x-6, node.y-6, node.x+6, node.y+6, fill="#10b981", outline="#34d399")
            node.label = self.canvas.create_text(node.x, node.y-15, text=f"ID:{node.id}", fill="#94a3b8", font=("Arial", 7))
            
            # Sağ paneldeki detay kartı
            card = tk.Frame(self.list_frame, bg="#1e293b", padx=10, pady=5, highlightbackground="#334155", highlightthickness=1)
            card.pack(fill="x", pady=2, padx=5)
            
            l1 = tk.Label(card, text=f"SENSÖR #{node.id}", font=("Arial", 9, "bold"), bg="#1e293b", fg="white")
            l1.pack(anchor="w")
            
            p_bar = ttk.Progressbar(card, length=250, mode="determinate")
            p_bar['value'] = 100
            p_bar.pack(pady=2)
            node.energy_bar = p_bar
            
            node.info_label = tk.Label(card, text="Enerji: 100J | Durum: AKTİF", font=("Arial", 8), bg="#1e293b", fg="#94a3b8")
            node.info_label.pack(anchor="w")
            
            self.nodes.append(node)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_btn.config(text="DEVAM ET" if self.is_paused else "DURDUR", bg="#10b981" if self.is_paused else "#1e293b")

    def trigger_leak(self):
        if self.leak_target:
            self.leak_target = None
            self.leak_btn.config(text="SIZINTI YAP", bg="#ef4444")
        else:
            self.leak_target = random.choice([n for n in self.nodes if n.is_active]).id
            self.leak_btn.config(text="ONAR", bg="#3b82f6")

    def update_simulation(self):
        if not self.is_paused:
            self.time_step += 1
            active_count = 0
            
            for node in self.nodes:
                if not node.is_active:
                    continue
                
                is_leak = node.id == self.leak_target
                dist = node.calculate_distance(BASE_STATION[0], BASE_STATION[1])
                
                # Enerji Tüketim Modeli
                base_consumption = 0.02 * node.flow_rate
                transmit_cost = 0.005 * (dist / 100)**2
                multiplier = 3.5 if is_leak else (1.5 if node.healing_mode else 1.0)
                
                node.energy -= (base_consumption + transmit_cost) * multiplier
                node.packets += 1
                
                if node.energy <= 0:
                    node.energy = 0
                    node.is_active = False
                    node.status = "ÖLÜ"
                    self.canvas.itemconfig(node.dot, fill="#334155", outline="#475569")
                    self.canvas.itemconfig(node.line, state="hidden")
                    if is_leak: self.leak_target = None
                else:
                    active_count += 1
                    # Renk güncelleme
                    color = "#ef4444" if is_leak else ("#f59e0b" if node.energy < 25 else "#10b981")
                    self.canvas.itemconfig(node.dot, fill=color)
                    
                    if is_leak:
                        # Yanıp sönen alarm efekti
                        current_color = self.canvas.itemcget(node.dot, "fill")
                        next_c = "#7f1d1d" if current_color == "#ef4444" else "#ef4444"
                        self.canvas.itemconfig(node.dot, fill=next_c)

                # UI Güncelleme
                node.energy_bar['value'] = node.energy
                node.info_label.config(text=f"Enerji: {node.energy:.1f}J | Veri: {node.packets} pkt", fg="#ef4444" if is_leak else "#94a3b8")

            self.stat_label.config(text=f"Süre: {self.time_step}s | Aktif Sensör: {active_count}/{NODE_COUNT}")

        # 500ms sonra tekrar çalıştır
        self.root.after(500, self.update_simulation)

if __name__ == "__main__":
    root = tk.Tk()
    app = WSNSimulator(root)
    root.mainloop()