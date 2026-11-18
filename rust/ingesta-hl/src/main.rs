use std::path::PathBuf;
use serde::Deserialize;

//--------------------------------------
//             CONSTANTES
//--------------------------------------

const URL_VAULTS: &str = "https://stats-data.hyperliquid.xyz/Mainnet/vaults";

//--------------------------------------
//             STRUCTS
//--------------------------------------

#[derive(Debug, Deserialize)]
struct Vault {
    apr: f64,
    pnls: Vec<(String, Vec<String>)>,
    summary: Resumen,
}

#[derive(Debug, Deserialize)]
struct Relacion {
    #[serde(rename = "type")]
    tipo: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all= "camelCase")]
struct Resumen {
    name: String,
    vault_address: String,
    leader: String,
    tvl: String,
    is_closed: bool,
    relationship: Relacion,
    create_time_millis: i64,
}

//--------------------------------------
//       DESCARGAR JSON DE VAULTS
//--------------------------------------

fn descargar(url: &str) -> Result<String, reqwest::Error> {
    reqwest::blocking::get(url)?.error_for_status()?.text()
}

//--------------------------------------
//                MAIN
//--------------------------------------

fn main() -> Result<(), Box<dyn std::error::Error>>{
    let hoy = chrono::Local::now().format("%Y-%m-%d").to_string();
    let carpeta = PathBuf::from("datos/crudo/hyperliquid").join(&hoy);
    let fichero = carpeta.join("vaults.json");

    println!("Descargando vaults de Hyperliquid");
    let texto = descargar(URL_VAULTS)?;

    let vaults: Vec<Vault> = serde_json::from_str(&texto)?;
    let cerrados = vaults.iter().filter(|v| v.summary.is_closed).count();
    println!("{} vaults válidos, {} cerrados", vaults.len(), cerrados);

    std::fs::create_dir_all(carpeta)?;
    std::fs::write(&fichero, &texto)?;
    println!("Guardados {} bytes en {}", texto.len(), fichero.display());

    Ok(())
}