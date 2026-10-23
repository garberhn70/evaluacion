import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const html = fs.readFileSync("index.html", "utf8");
const checks = [];
function check(name, fn) {
  try { fn(); checks.push({ name, ok: true }); }
  catch (error) { checks.push({ name, ok: false, error: error.message }); }
}
function has(re, message) { assert.match(html, re, message); }

check("index.html existe y no está vacío", () => assert.ok(html.length > 100000));
check("Puerta de acceso Supabase presente", () => {
  for (const id of ["cloudAuthGate", "cloudProjectUrl", "cloudAnonKey", "cloudEmail", "cloudPassword", "cloudLicense", "cloudSignIn", "cloudSignUp", "cloudSignOut"])
    assert.ok(html.includes('id="' + id + '"'), "Falta elemento #" + id);
});
check("Registro, cámara y reportes tienen controles", () => {
  for (const id of ["athletePhotoPreview", "athleteCameraStart", "athleteCameraCapture", "athletePhotoUpload", "pdfTeam", "resetAllData", "resetAllToast"])
    assert.ok(html.includes('id="' + id + '"'), "Falta elemento #" + id);
});
check("Autenticación incluye inicio de sesión y recuperación", () => {
  has(/signInWithPassword\s*\(/, "No se encontró signInWithPassword");
  has(/signUp\s*\(/, "No se encontró signUp");
  has(/resetPasswordForEmail\s*\(/, "No se encontró recuperación de contraseña");
});
check("Activación de licencia usa RPC esperado", () => has(/rpc\('activate_device_license'/, "No se encontró la validación de licencia"));
check("Registros de nube están limitados al usuario autenticado", () => {
  has(/from\('app_records'\)\.select\('collection,record_id,data'\)\.eq\('user_id',window\.vbUser\.id\)/, "La lectura no limita por user_id");
  has(/from\('app_records'\)\.upsert\(/, "No se encontró upsert de registros");
});
check("Restablecimiento exige dos confirmaciones y limita el borrado a la cuenta", () => {
  has(/resetAllData'\)\.onclick=async/, "No se encontró el manejador del botón");
  has(/confirm\('ATENCIÓN:[\s\S]{0,500}\)return;/, "No se encontró confirmación inicial");
  has(/prompt\('Para confirmar, escriba BORRAR en mayúsculas:'\)!=='BORRAR'/, "No se requiere la palabra BORRAR");
  has(/from\('app_records'\)\.delete\(\)\.eq\('user_id',window\.vbUser\.id\)/, "El borrado en nube no se limita por user_id");
});
check("Captura de cámara y compresión de imagen existen", () => {
  has(/getUserMedia\s*\(/, "No se encontró acceso a cámara");
  has(/function imageToCompactData\s*\(/, "No se encontró compresión de imagen");
  has(/athletePhotoData/, "No se encontró estado de fotografía");
});
check("El flujo de informe del equipo existe", () => has(/pdfTeam['"]?\)?\.onclick=teamPDF|\$\('pdfTeam'\)\.onclick=teamPDF/, "No se encontró acción PDF de equipo"));
check("No se incrusta una clave service_role conocida en el HTML", () => {
  assert.doesNotMatch(html, /(?:service_role|SUPABASE_SERVICE_ROLE_KEY)\s*[:=]\s*['"][^'"]{12,}/i,
    "Parece existir una asignación de clave privilegiada en el HTML");
});
check("Todos los bloques JavaScript embebidos pasan el análisis de sintaxis", () => {
  const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
    .filter(match => !/\bsrc\s*=/.test(match[1]));
  assert.ok(scripts.length >= 4, "Se encontraron muy pocos scripts embebidos");
  scripts.forEach((match, index) => new vm.Script(match[2], { filename: "index.html:inline-script-" + index }));
});
check("Manifiesto JSON y recursos principales están presentes", () => {
  const manifestTag = html.match(/<link[^>]+rel=["']manifest["'][^>]+href=["']([^"']+)["']/i);
  assert.ok(manifestTag, "No se encontró referencia al manifiesto");
  const manifestPath = manifestTag[1].replace(/^\.\//, "");
  assert.ok(fs.existsSync(manifestPath), "No existe " + manifestPath);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  assert.ok(manifest.name || manifest.short_name, "El manifiesto no tiene nombre");
  assert.ok(fs.existsSync("sw.js"), "No existe sw.js");
  assert.ok(fs.existsSync("icon.svg"), "No existe icon.svg");
});

check("El código de licencia se lee como texto (no JSON)", () => {
  assert.doesNotMatch(html, /local\.get\('vb-license-code'/, "La licencia se lee con local.get (JSON.parse) y siempre queda vacía");
  has(/localStorage\.getItem\('vb-license-code'\)/, "No se encontró la lectura de la licencia");
});
check("El tipo de dispositivo se conserva después de recargar", () => has(/localStorage\.setItem\('vb-device-type'/, "El tipo de dispositivo no se guarda"));
check("«Elegir fotografía» permite usar la galería en celulares", () =>
  assert.doesNotMatch(html, /id="athletePhotoUpload"[^>]*capture=/, "El selector tiene capture y abre solo la cámara"));

const failed = checks.filter(item => !item.ok);
for (const result of checks)
  console.log((result.ok ? "PASS" : "FAIL") + "  " + result.name + (result.error ? "\n      " + result.error : ""));
console.log("\nResultado: " + (checks.length - failed.length) + "/" + checks.length + " comprobaciones estáticas aprobadas.");
if (failed.length) process.exitCode = 1;
