import tkinter as tk
from tkinter import messagebox
from login.auth_manager import AuthManager



class LoginUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - FitPal")
        self.auth = AuthManager()

        self.frame = tk.Frame(self.root, padx=20, pady=20)
        self.frame.pack(expand=True)

        # Email label and input
        tk.Label(self.frame, text="Email:").grid(row=0, column=0, sticky="e")
        self.email_entry = tk.Entry(self.frame, width=30)
        self.email_entry.grid(row=0, column=1, pady=5)

        # Password label and input
        tk.Label(self.frame, text="Password:").grid(row=1, column=0, sticky="e")
        self.password_entry = tk.Entry(self.frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, pady=5)

        # Login button
        self.login_btn = tk.Button(self.frame, text="Login", command=self.login)
        self.login_btn.grid(row=2, columnspan=2, pady=10)

        # Signup link
        self.signup_btn = tk.Button(self.frame, text="Sign Up", command=self.signup)
        self.signup_btn.grid(row=3, columnspan=2)

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        result = self.auth.login(email, password)

        if isinstance(result, dict):
            messagebox.showinfo("Login Successful", f"Welcome, {email}!")
            self.open_main_app()  # Replace this with your real function
        else:
            messagebox.showerror("Login Failed", result)

    def signup(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        result = self.auth.signup(email, password)

        if isinstance(result, dict):
            messagebox.showinfo("Signup Successful", f"Account created for {email}!")
        else:
            messagebox.showerror("Signup Failed", result)

    def open_main_app(self):
        # Placeholder — replace with code to open your avatar/wardrobe app
        self.frame.destroy()
        tk.Label(self.root, text="Welcome to FitPal!", font=("Arial", 18)).pack(pady=50)


# Run the UI
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginUI(root)
    root.mainloop()
