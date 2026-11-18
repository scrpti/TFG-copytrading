use std::path::PathBuf;

const URL_VAULTS: &str = "https://stats-data.hyperliquid.xyz/Mainnet/vaults";

fn descargar(url: &str) -> Result<String, reqwest::Error> {
    let respuesta = reqwest::blocking::get(url)?.error_for_status()?.text();
    respuesta
}

fn main() -> Result<(), Box<dyn std::error::Error>>{
    let hoy = chrono::Local::now().format("%Y-%m-%d").to_string();
    let carpeta = PathBuf::from("datos/crudo/hyperliquid").join(&hoy);
    let fichero = carpeta.join("vaults.json");

    println!("Descargando vaults de Hyperliquid");
    let texto = descargar(URL_VAULTS)?;

    std::fs::create_dir_all(carpeta)?;
    std::fs::write(&fichero, &texto)?;
    println!("Guardados {} bytes en {}", texto.len(), fichero.display());

    Ok(())
}