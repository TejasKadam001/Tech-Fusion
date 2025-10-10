const canvas = document.getElementById("stars");
const ctx = canvas.getContext("2d");

function setupStars() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const density = 0.05;
  const starCount = Math.floor(canvas.width * density);

  const stars = Array.from({ length: starCount }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    z: Math.random() * canvas.width,
    radius: Math.random() * 0.4 + 0.2,
  }));

  return stars;
}

let stars = setupStars();

function resetStar(star) {
  star.x = Math.random() * canvas.width;
  star.y = Math.random() * canvas.height;
  star.z = canvas.width;
  star.radius = Math.random() * 0.8 + 0.2;
}

function drawStars() {
  ctx.fillStyle = "black";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const cx = canvas.width / 2;
  const cy = canvas.height / 2;

  stars.forEach((star) => {
    const dx = star.x - cx;
    const dy = star.y - cy;
    const perspective = canvas.width / (canvas.width + star.z);
    const x = cx + dx * perspective;
    const y = cy + dy * perspective;
    const radius = star.radius * perspective * 2;

    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = "white";
    ctx.shadowBlur = 6;
    ctx.shadowColor = "white";
    ctx.fill();
  });
}

function updateStars() {
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;

  stars.forEach((star) => {
    const dx = star.x - cx;
    const dy = star.y - cy;
    const dist = Math.sqrt(dx * dx + dy * dy);

    const speed = 5 + dist / 480;
    star.z -= speed;

    if (star.z <= 1) {
      resetStar(star);
    }
  });
}

function resizeCanvas() {
  stars = setupStars();
}

window.addEventListener("resize", resizeCanvas);

function animate() {
  drawStars();
  updateStars();
  requestAnimationFrame(animate);
}

animate();