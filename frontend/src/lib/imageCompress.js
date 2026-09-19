/* Helpers pour compression/redimensionnement d'images côté client.

   But : éviter d'uploader des photos 4 Mo en base64 en DB.
   On redimensionne à 1280px max (côté le plus long) + qualité JPEG 0.82
   → résultat typique : 200-450 Ko (vs 3-4 Mo en source).
*/

/**
 * Lit un File et le redimensionne via Canvas.
 * Retourne { dataUrl, b64, mime, sizeKb }.
 *
 * @param {File} file
 * @param {{maxSide?: number, quality?: number}} opts
 */
export async function compressImage(file, opts = {}) {
  const maxSide = opts.maxSide || 1280;
  const quality = opts.quality ?? 0.82;

  // 1) Charger l'image
  const dataUrl0 = await readAsDataURL(file);
  const img = await loadImage(dataUrl0);

  // 2) Calculer nouvelle taille (côté le plus long = maxSide)
  let { width, height } = img;
  if (width > maxSide || height > maxSide) {
    if (width >= height) {
      height = Math.round((height * maxSide) / width);
      width = maxSide;
    } else {
      width = Math.round((width * maxSide) / height);
      height = maxSide;
    }
  }

  // 3) Dessiner sur un canvas
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, width, height);

  // 4) Toujours sortir en JPEG (sauf PNG transparent — rare pour des photos)
  const mime = "image/jpeg";
  const dataUrl = canvas.toDataURL(mime, quality);
  const b64 = dataUrl.split(",")[1];
  const sizeKb = Math.round((b64.length * 3) / 4 / 1024);

  return { dataUrl, b64, mime, sizeKb, width, height };
}

function readAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}
