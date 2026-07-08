import customtkinter as ctk
import requests
import os
import threading
from duckduckgo_search import DDGS

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat IA - Modern & Web-Enabled")
        self.root.geometry("650x750")

        # Configurar tema do CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configurar chave da API
        self.api_key = os.environ.get("NVIDIA_API_KEY", "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")
        self.invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.messages_history = [
            {
                "role": "system", 
                "content": "Você é a Alegria, a emoção principal do filme Divertida Mente. Você é extremamente otimista, radiante, energética e sempre vê o lado bom de absolutamente tudo! Responda com muito entusiasmo, alegria, exclamativas e positividade contagiante! Use emojis felizes."
            }
        ]

        self.setup_ui()

    def setup_ui(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)

        # Área de texto rolável para histórico
        self.chat_display = ctk.CTkTextbox(
            self.main_frame, 
            wrap="word", 
            state="disabled", 
            font=("Segoe UI", 15),
            fg_color="#1E1E1E",
            text_color="#FFFFFF",
            corner_radius=10
        )
        self.chat_display.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True, pady=(0, 20))

        # Configurar tags para cores e alinhamento usando o objeto interno tk.Text
        self.chat_display._textbox.tag_config("user", foreground="#4DA8DA", justify="right")
        self.chat_display._textbox.tag_config("assistant", foreground="#E8E8E8", justify="left")
        self.chat_display._textbox.tag_config("system", foreground="#888888", justify="center")
        self.chat_display._textbox.tag_config("error", foreground="#FF6B6B", justify="center")

        # Frame inferior para entrada
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.pack(side=ctk.BOTTOM, fill=ctk.X)

        self.user_input = ctk.CTkEntry(
            self.input_frame, 
            font=("Segoe UI", 15),
            placeholder_text="Pergunte qualquer coisa (inclusive fatos atuais)...",
            height=45,
            corner_radius=20
        )
        self.user_input.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", lambda event: self.send_message_click())

        self.send_button = ctk.CTkButton(
            self.input_frame, 
            text="Enviar", 
            command=self.send_message_click,
            font=("Segoe UI", 15, "bold"),
            height=45,
            corner_radius=20,
            width=110
        )
        self.send_button.pack(side=ctk.RIGHT)

        self.user_input.focus()

    def add_message(self, role, text):
        self.chat_display.configure(state="normal")
        
        if role == "user":
            self.chat_display._textbox.insert("end", "Você:\n", "user")
            self.chat_display._textbox.insert("end", text + "\n\n", "user")
        elif role == "assistant":
            self.chat_display._textbox.insert("end", "IA:\n", "assistant")
            self.chat_display._textbox.insert("end", text + "\n\n", "assistant")
        elif role == "system":
            self.chat_display._textbox.insert("end", text + "\n\n", "system")
        else:
            self.chat_display._textbox.insert("end", text + "\n\n", "error")
            
        self.chat_display.configure(state="disabled")
        self.chat_display.yview("end")

    def perform_web_search(self, query):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if not results:
                    return ""
                
                context = "Resultados recentes da internet:\n"
                for res in results:
                    context += f"- {res['title']}: {res['body']}\n"
                return context
        except Exception as e:
            print(f"Erro na pesquisa web: {e}")
            return ""

    def send_message_click(self):
        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.user_input.delete(0, "end")
        self.user_input.configure(state="disabled")
        self.send_button.configure(state="disabled")

        self.add_message("user", user_text)

        # Iniciar thread para pesquisa + API para não travar a UI
        threading.Thread(target=self.process_request, args=(user_text,), daemon=True).start()

    def process_request(self, user_text):
        self.root.after(0, self.add_message, "system", "[Pesquisando na web por informações recentes...]")
        
        # 1. Faz a pesquisa na internet
        web_context = self.perform_web_search(user_text)
        
        # 2. Prepara as mensagens
        # Adiciona a mensagem do usuário ao histórico (sem o contexto gigante para não poluir)
        self.messages_history.append({"role": "user", "content": user_text})
        
        # Prepara um histórico temporário onde injetamos o contexto da web na última mensagem
        temp_history = list(self.messages_history)
        if web_context:
            prompt_with_context = f"Responda à pergunta do usuário. Use as informações a seguir obtidas da web para fatos recentes (depois de 2024), se forem relevantes. Não precisa mencionar que você pesquisou, apenas aja como se soubesse a resposta.\n\n{web_context}\n\nPergunta do usuário: {user_text}"
            temp_history[-1] = {"role": "user", "content": prompt_with_context}

        # 3. Faz a requisição para a IA
        self.fetch_response(temp_history)

    def fetch_response(self, messages_payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        payload = {
            "model": "z-ai/glm-5.2",
            "messages": messages_payload,
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": False,
        }

        try:
            response = requests.post(self.invoke_url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                ai_text = response_json["choices"][0]["message"]["content"]
                # Adiciona a resposta da IA no histórico real
                self.messages_history.append({"role": "assistant", "content": ai_text})
                # Atualiza a interface gráfica
                self.root.after(0, self.add_message, "assistant", ai_text)
            else:
                self.root.after(0, self.add_message, "error", "Erro: Resposta inesperada da API.")
                
        except Exception as ex:
            self.root.after(0, self.add_message, "error", f"Erro ao conectar com a API: {str(ex)}")

        finally:
            self.root.after(0, self.enable_input)

    def enable_input(self):
        self.user_input.configure(state="normal")
        self.send_button.configure(state="normal")
        self.user_input.focus()

if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatApp(root)
    root.mainloop()
