import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import json
import sys
from decryption import decrypt_file
from s3_downloader import get_s3_objects, download_from_s3

class S3DriveDecryptor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("S3Drive Replica - Secure Decryptor [v0.1.4]")
        self.geometry("600x800")
        
        # WHITE THEME 🤍
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # UI State
        self.selected_objects = []

        # --- PERMANENT CONFIG STORAGE ---
        self.app_data_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), "S3DriveReplica")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.config_file = os.path.join(self.app_data_dir, "decryptor_config.json")
        self.log_file_path = os.path.join(self.app_data_dir, "decrypt_log.txt")

        # --- UI LAYOUT ---
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(pady=0, padx=0, fill="both", expand=True)
        
        # Connection Frame
        self.conn_frame = ctk.CTkFrame(self.main_container)
        self.conn_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.conn_frame, text="AWS S3 Connection", font=("Arial", 16, "bold")).pack(pady=5)
        self.access_key = self.create_input(self.conn_frame, "AWS Access Key")
        self.secret_key = self.create_input(self.conn_frame, "AWS Secret Key", show="*")
        self.bucket_name = self.create_input(self.conn_frame, "S3 Bucket/Path (ARN)")
        self.region = self.create_input(self.conn_frame, "Region (e.g. us-east-1)", default="ap-southeast-1")

        # Security Frame
        self.sec_frame = ctk.CTkFrame(self.main_container)
        self.sec_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.sec_frame, text="Decryption Key", font=("Arial", 16, "bold")).pack(pady=5)
        self.dec_mode = ctk.CTkSegmentedButton(self.sec_frame, values=["Symmetric", "Asymmetric"])
        self.dec_mode.set("Symmetric")
        self.dec_mode.pack(pady=5)
        self.key_input = ctk.CTkTextbox(self.sec_frame, height=100)
        self.key_input.pack(pady=10, padx=10, fill="x")
        self.key_input.insert("1.0", "Enter Passphrase or Private Key here...")

        # S3 List Frame
        self.list_frame = ctk.CTkFrame(self.main_container)
        self.list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        ctk.CTkLabel(self.list_frame, text="S3 Objects", font=("Arial", 16, "bold")).pack(pady=5)
        self.btn_fetch = ctk.CTkButton(self.list_frame, text="Fetch S3 List", command=self.fetch_objects)
        self.btn_fetch.pack(pady=5)
        self.object_listbox = ctk.CTkScrollableFrame(self.list_frame, height=200)
        self.object_listbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.checkboxes = {}

        # ACTION BUTTONS
        self.btn_decrypt = ctk.CTkButton(self.main_container, text="DOWNLOAD & DECRYPT", fg_color="blue", 
                                         hover_color="darkblue", command=self.start_decrypt_thread, font=("Arial", 14, "bold"))
        self.btn_decrypt.pack(pady=(20, 5))
        self.btn_save_config = ctk.CTkButton(self.main_container, text="Save Configuration", fg_color="blue", 
                                            hover_color="darkblue", command=self.save_config, font=("Arial", 12))
        self.btn_save_config.pack(pady=5)

        # Log
        ctk.CTkLabel(self.main_container, text="Activity Log", font=("Arial", 12, "bold")).pack(pady=(10, 0))
        self.log = ctk.CTkTextbox(self.main_container, height=150)
        self.log.pack(pady=10, padx=20, fill="x")
        
        self.load_config()
        self.write_log("Ready to decrypt! ✨")

    def create_input(self, parent, label, show=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(frame, text=label, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, show=show)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def write_log(self, text):
        self.after(0, lambda: self._do_write_log(text))
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(f"{text}\n")
        except:
            pass

    def _do_write_log(self, text):
        self.log.insert("end", f"{text}\n")
        self.log.see("end")

    def fetch_objects(self):
        access = self.access_key.get()
        secret = self.secret_key.get()
        bucket = self.bucket_name.get()
        region = self.region.get()
        if not all([access, secret, bucket, region]):
            messagebox.showerror("Error", "Please fill in all connection details!")
            return
        self.write_log("Fetching list from S3... ☁️")
        objects, err = get_s3_objects(bucket, access, secret, region)
        if err:
            self.write_log(f"Error: {err} ❌")
            return
        for widget in self.object_listbox.winfo_children():
            widget.destroy()
        self.checkboxes = {}
        if not objects:
            self.write_log("No objects found in bucket. 📦")
            return
        for obj in objects:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(self.object_listbox, text=obj, variable=var)
            cb.pack(anchor="w", padx=10, pady=2)
            self.checkboxes[obj] = var
        self.write_log(f"Found {len(objects)} objects. ✅")

    def start_decrypt_thread(self):
        self.save_config()
        self.log.delete("1.0", "end")
        self.write_log("Starting decryption process... 🚀")
        threading.Thread(target=self.process_decryption, daemon=True).start()

    def process_decryption(self):
        access = self.access_key.get()
        secret = self.secret_key.get()
        bucket = self.bucket_name.get()
        region = self.region.get()
        key_data = self.key_input.get("1.0", "end-1c").strip()
        if not all([access, secret, bucket, region, key_data]):
            self.after(0, lambda: messagebox.showerror("Error", "Please fill in all connection and decryption details!"))
            return
        selected = [obj for obj, var in self.checkboxes.items() if var.get()]
        if not selected:
            self.after(0, lambda: messagebox.showerror("Error", "Please select at least one file to decrypt!"))
            return
        mode = self.dec_mode.get()
        success_count, fail_count = 0, 0
        for obj_name in selected:
            try:
                self.write_log(f"Downloading {obj_name}... 🚀")
                blob, err = download_from_s3(bucket, obj_name, access, secret, region)
                if err:
                    self.write_log(f"Download failed for {obj_name}: {err} ❌")
                    fail_count += 1; continue
                if mode == "Symmetric":
                    plaintext = decrypt_file(blob, passphrase=key_data)
                else:
                    plaintext = decrypt_file(blob, private_key=key_data)
                out_name = obj_name[:-4] if (obj_name.endswith(".enc") or obj_name.endswith(".pgp")) else obj_name
                with open(out_name, "wb") as f:
                    f.write(plaintext)
                self.write_log(f"Successfully decrypted {obj_name} -> {out_name} ✅")
                success_count += 1
            except Exception as e:
                self.write_log(f"Error decrypting {obj_name}: {str(e)} ❌")
                fail_count += 1
        self.after(0, lambda: messagebox.showinfo("Finished", f"Process completed!\n\n✅ Success: {success_count}\n❌ Failed: {fail_count}"))

    def save_config(self):
        config = {
            "access_key": self.access_key.get(),
            "bucket_name": self.bucket_name.get(),
            "region": self.region.get(),
            "dec_mode": self.dec_mode.get(),
            "key_data": self.key_input.get("1.0", "end-1c").strip()
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                self.access_key.insert(0, config.get("access_key", ""))
                self.bucket_name.insert(0, config.get("bucket_name", ""))
                self.region.insert(0, config.get("region", ""))
                self.dec_mode.set(config.get("dec_mode", "Symmetric"))
                self.key_input.delete("1.0", "end")
                self.key_input.insert("1.0", config.get("key_data", ""))
            except Exception as e:
                print(f"Failed to load config: {e}")

if __name__ == "__main__":
    app = S3DriveDecryptor()
    app.mainloop()
