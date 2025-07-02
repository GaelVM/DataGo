from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Usa webdriver-manager para resolver versiones automáticamente
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Cargar la página
driver.get("https://pokemongolive.com/news/?hl=es")
time.sleep(3)  # Esperar carga de JavaScript

# Buscar publicaciones
posts = driver.find_elements(By.CSS_SELECTOR, ".blogList__post")

posts_data = []
for post in posts:
    try:
        post_url = post.get_attribute("href")
        post_image = post.find_element(By.TAG_NAME, "img").get_attribute("src")
        post_date = post.find_element(By.CLASS_NAME, "blogList__post__content__date").text.strip()
        post_title = post.find_element(By.CLASS_NAME, "blogList__post__content__title").text.strip()

        posts_data.append({
            "URL": post_url,
            "Image": post_image,
            "Date": post_date,
            "Title": post_title
        })
    except Exception as e:
        print(f"Error en una entrada: {e}")

driver.quit()

# Guardar a JSON
os.makedirs("temp", exist_ok=True)
with open("temp/noticias.json", "w", encoding="utf-8") as f:
    json.dump(posts_data, f, ensure_ascii=False, indent=2)

print("✅ Noticias guardadas en temp/noticias.json")
