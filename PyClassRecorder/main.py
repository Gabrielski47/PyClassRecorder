import pyautogui as pag
import time
import threading
import keyboard
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
import re
import requests
import pygetwindow as gw

# === CONFIGS ===

email = "gabriel@gmail.com" #(O email de acesso esta generica pra evitar acesso a minha conta)
senha = "1234" #(A senha de acesso esta generica pra evitar acesso a minha conta)
fullscreen_coords = (1127, 663)
fechar_aba_coords = (1338, 116)
inicio_video_coords = (22, 705)
play_video_coords = (25, 743)
centro_tela = (680, 360)

stop_flag = {"should_stop": False}
aulas_gravadas = 0
obs_aberto = False
MODO_TESTE = {"ativo": False}
PASTA_TXT = {"caminho": os.path.join(os.getcwd(), "aulas_texto")}
INTERVALO_AULAS = {"inicio": 1, "fim": None}

def monitorar_tecla_break():
    keyboard.wait("b")
    stop_flag["should_stop"] = True

threading.Thread(target=monitorar_tecla_break, daemon=True).start()

def clicar_em_coordenada(x, y, duration=0):
    pag.moveTo(x, y, duration=duration)
    pag.click()

def obs_esta_aberto():
    return any("obs" in w.title.lower() or "obs" in w._hWnd.__str__().lower() 
               for w in gw.getWindowsWithTitle("OBS"))

def focar_obs():
    for window in gw.getWindowsWithTitle("OBS"):
        if window.isMinimized:
            window.restore()
        window.activate()
        return True
    return False

def extrair_aulas_e_duracoes(url):
    print(f"🔎 Analisando página: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    cards = soup.select("a.class")
    aulas = []
    duracoes = []

    for card in cards:
        href = card.get("href", "")
        if not href.startswith("/aulas/"):
            continue
        link = f"https://padrepauloricardo.org{href}"
        duracao_tag = card.select_one(".class__duration")
        if duracao_tag:
            tempo = duracao_tag.get_text().strip()
            partes = tempo.split(":")
            segundos = sum(int(x) * 60 ** (len(partes)-i-1) for i, x in enumerate(partes))
            aulas.append(link)
            duracoes.append(segundos)

    print(f"✅ {len(aulas)} aulas detectadas.")
    return aulas, duracoes


def salvar_texto_aula(driver, link, titulo, indice):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section.lesson-text"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        header = soup.select_one("section.lesson-text header")
        conteudo = soup.select_one("article.lesson-text__editor")
        referencias = soup.select("footer.references")

        partes = []
        if header:
            partes.append(header.get_text(separator="\n", strip=True))
        if conteudo:
            partes.append(conteudo.get_text(separator="\n", strip=True))

        for ref in referencias:
            subtitulo = ref.select_one("h3.references__subtitle")
            lista = ref.select_one("div.references__list")
            bloco = []
            if subtitulo:
                bloco.append(f"\n{subtitulo.get_text(strip=True)}:")
            if lista:
                for item in lista.find_all(["p", "li"]):
                    texto = item.get_text(strip=True)
                    if texto:
                        bloco.append(texto)
            if bloco:
                partes.append("\n".join(bloco))

        texto_completo = "\n\n".join(partes)
        titulo_limpo = re.sub(r'[\\/:*?"<>|]', '', titulo)
        nome_arquivo = f"{indice:02d} - {titulo_limpo}.txt"
        caminho = os.path.join(PASTA_TXT["caminho"], nome_arquivo)

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto_completo)

        print(f"📄 Texto salvo: {nome_arquivo}")

    except Exception as e:
        print(f"⚠️ Erro ao salvar texto da aula {indice}: {e}")


def fechar_janela_avaliacao(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "course-review__next-button"))
        )
        print("🟡 Janela de avaliação detectada.")
        time.sleep(2)
        driver.find_element(By.CLASS_NAME, "course-review__next-button").click()
        print("➡️ Clicou em 'Próximo'")

        time.sleep(2)
        driver.find_element(By.CLASS_NAME, "course-review__send-button").click()
        print("📨 Clicou em 'Enviar'")

        time.sleep(2)
        driver.find_element(By.CLASS_NAME, "course-review__close-icon").click()
        print("❌ Clicou no 'X' para fechar a janela")
    except:
        pass  # Janela não apareceu


def iniciar_gravacao(url):
    global aulas_gravadas, obs_aberto
    aulas_gravadas = 0
    obs_aberto = False
    stop_flag["should_stop"] = False

    aulas, duracoes = extrair_aulas_e_duracoes(url)
    if not aulas:
        messagebox.showerror("Erro", "Não foi possível extrair aulas dessa URL.")
        return

    inicio = INTERVALO_AULAS["inicio"] - 1
    fim = INTERVALO_AULAS["fim"] or len(aulas)
    aulas = aulas[inicio:fim]
    duracoes = duracoes[inicio:fim]

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    driver.get("https://padrepauloricardo.org/entrar")
    time.sleep(1)
    clicar_em_coordenada(*fechar_aba_coords)

    try:
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        senha_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        email_input.send_keys(email)
        senha_input.send_keys(senha)
        senha_input.send_keys(Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.url_changes("https://padrepauloricardo.org/entrar"))
    except:
        print("❌ Erro no login")
        driver.quit()
        return

    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Aceito Tudo")]'))
        ).click()
    except:
        pass

    driver.get(url)
    time.sleep(4)

    for i, (link, duracao_real) in enumerate(
        zip(aulas, duracoes), start=INTERVALO_AULAS["inicio"]
    ):
        duracao = 5 if MODO_TESTE["ativo"] else duracao_real

        if stop_flag["should_stop"]:
            print(f"🟥 Interrompido! Aula que parou: {link}")
            break

        driver.get(link)
        print(f"\n📘 Aula {i}: {link}")
        time.sleep(7)

        # =====================================================
        # 🔽 **SCROLL AUTOMÁTICO NOVO** após carregar a página
        # =====================================================
        try:
            black_section = driver.find_element(By.CLASS_NAME, "black-section")
            altura_banner = black_section.size["height"]
            driver.execute_script(f"window.scrollBy(0, {altura_banner});")
            print(f"🔽 Rolagem automática aplicada: {altura_banner}px")
        except:
            print("⚠️ Banner .black-section não encontrado. Nenhum scroll aplicado.")
        # =====================================================

        fechar_janela_avaliacao(driver)

        try:
            titulo_tag = driver.find_element(By.CSS_SELECTOR, "h2.lesson-text__title")
            titulo = titulo_tag.text.strip()
            salvar_texto_aula(driver, link, titulo, i)

            if i == INTERVALO_AULAS["inicio"]:
                if obs_esta_aberto():
                    print("OBS já está aberto. Colocando em primeiro plano...")
                    focar_obs()
                    time.sleep(1)
                else:
                    print("Abrindo OBS Studio...")
                    pag.press("win")
                    time.sleep(2)
                    pag.write("OBS Studio")
                    time.sleep(2)
                    pag.press("enter")
                    time.sleep(15)
                obs_aberto = True
            else:
                pag.hotkey("alt", "tab")

            pag.press("f9")
            pag.hotkey("alt", "tab")
            clicar_em_coordenada(*fullscreen_coords)
            time.sleep(0.5)
            clicar_em_coordenada(*inicio_video_coords)
            clicar_em_coordenada(*play_video_coords)
            time.sleep(0.5)
            pag.moveTo(*centro_tela)

            print(f"Aguardando {duracao} segundos...")
            time.sleep(duracao + 5)

            pag.press("esc")
            pag.hotkey("alt", "tab")
            pag.press("f10")
            pag.hotkey("alt", "tab")

            aulas_gravadas += 1

        except Exception as e:
            print(f"Erro na aula: {e}")
            break

    driver.quit()
    mostrar_interface_final()


def mostrar_interface_final():
    def novo_curso():
        root.withdraw()
        nova_url = simpledialog.askstring("Novo curso", "Digite a nova URL:")
        if nova_url:
            try:
                INTERVALO_AULAS["inicio"] = int(entry_inicio.get())
                fim = entry_fim.get().strip()
                INTERVALO_AULAS["fim"] = int(fim) if fim else None
            except ValueError:
                messagebox.showerror("Erro", "Insira números válidos para o intervalo.")
                root.deiconify()
                return
            root.destroy()
            iniciar_gravacao(nova_url)
        else:
            root.deiconify()

    def alternar_modo():
        MODO_TESTE["ativo"] = not MODO_TESTE["ativo"]
        btn_modo.config(text="Modo Teste: ATIVADO" if MODO_TESTE["ativo"] else "Modo Teste: DESATIVADO")

    def escolher_pasta_final():
        nova = filedialog.askdirectory()
        if nova:
            PASTA_TXT["caminho"] = nova
            messagebox.showinfo("Pasta", f"Pasta escolhida: {PASTA_TXT['caminho']}")

    root = tk.Tk()
    root.title("Finalizado")
    root.geometry("420x300")
    root.attributes('-topmost', True)

    tk.Label(root, text="Todas as aulas foram gravadas com sucesso!", font=("Arial", 12)).pack(pady=10)

    tk.Label(root, text="Início da aula:").pack()
    entry_inicio = tk.Entry(root)
    entry_inicio.pack()
    entry_inicio.insert(0, str(INTERVALO_AULAS["inicio"]))

    tk.Label(root, text="Fim da aula (em branco = até o fim):").pack()
    entry_fim = tk.Entry(root)
    entry_fim.pack()
    entry_fim.insert(0, "" if INTERVALO_AULAS["fim"] is None else str(INTERVALO_AULAS["fim"]))

    tk.Button(root, text="Gravar novo curso", command=novo_curso, width=25).pack(pady=5)
    btn_modo = tk.Button(root, text="Modo Teste: ATIVADO" if MODO_TESTE["ativo"] else "Modo Teste: DESATIVADO",
                         command=alternar_modo, width=25)
    btn_modo.pack(pady=5)
    tk.Button(root, text="Escolher pasta para os textos", command=escolher_pasta_final, width=25).pack(pady=5)
    tk.Button(root, text="Encerrar", command=root.destroy, width=25).pack(pady=5)

    root.mainloop()


def interface_inicial():
    def confirmar():
        url = entry.get().strip()
        if not url or not url.startswith("https://padrepauloricardo.org/cursos/"):
            messagebox.showerror("Erro", "Digite uma URL válida.")
            return
        try:
            INTERVALO_AULAS["inicio"] = int(entry_inicio.get())
            fim = entry_fim.get().strip()
            INTERVALO_AULAS["fim"] = int(fim) if fim else None
        except ValueError:
            messagebox.showerror("Erro", "Insira números válidos para o intervalo de aulas.")
            return
        root.destroy()
        iniciar_gravacao(url)

    def alternar_modo():
        MODO_TESTE["ativo"] = not MODO_TESTE["ativo"]
        btn_modo.config(text="Modo Teste: ATIVADO" if MODO_TESTE["ativo"] else "Modo Teste: DESATIVADO")

    def escolher_pasta_inicial():
        pasta = filedialog.askdirectory()
        if pasta:
            PASTA_TXT["caminho"] = pasta
            messagebox.showinfo("Pasta", f"Pasta escolhida: {pasta}")

    root = tk.Tk()
    root.title("Iniciar Gravação")
    root.geometry("420x260")
    root.attributes('-topmost', True)

    tk.Label(root, text="Digite a URL do curso:", font=("Arial", 11)).pack(pady=5)
    entry = tk.Entry(root, width=60)
    entry.pack()
    entry.insert(0, "https://padrepauloricardo.org/cursos/inquisicao")

    tk.Label(root, text="Início da aula:").pack()
    entry_inicio = tk.Entry(root)
    entry_inicio.pack()
    entry_inicio.insert(0, "1")

    tk.Label(root, text="Fim da aula (em branco = até o fim):").pack()
    entry_fim = tk.Entry(root)
    entry_fim.pack()

    tk.Button(root, text="Confirmar", command=confirmar, width=25).pack(pady=5)
    btn_modo = tk.Button(root, text="Modo Teste: DESATIVADO", command=alternar_modo, width=25)
    btn_modo.pack(pady=2)
    tk.Button(root, text="Escolher pasta para os textos", command=escolher_pasta_inicial, width=25).pack(pady=2)
    root.mainloop()


interface_inicial()


