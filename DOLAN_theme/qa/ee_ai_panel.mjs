import { chromium } from "playwright";
const b = await chromium.connectOverCDP("http://127.0.0.1:9223");
const ctx = b.contexts()[0];
const page = ctx.pages().find(p => p.url().includes("exalink"));
await page.locator('[title="Preguntar a la IA"]').first().click();
await page.waitForTimeout(6000);
const panel = await page.evaluate(() => {
  const aside = document.querySelector(".o_ai_panel, [class*=ai_panel], [class*=ai-], aside, .o_chat_panel");
  const candidates = [...document.querySelectorAll("div[class]")].filter(d => /ai/i.test(d.className) && d.getBoundingClientRect().width > 200).slice(0, 5)
    .map(d => ({ cls: d.className.toString().slice(0, 80), w: Math.round(d.getBoundingClientRect().width) }));
  const composer = !!document.querySelector("[placeholder*='Mensaje'], [placeholder*='pregunt'], [placeholder*='IA']");
  return { aside: aside ? aside.className.toString().slice(0, 80) : null, candidates, composer };
});
console.log("PANEL:", JSON.stringify(panel).slice(0, 700));
await page.screenshot({ path: "/root/DOLAN_odoo20/DOLAN_theme/qa/shots/l34-ee-ia-panel.png" });
// escribir un mensaje de prueba para ver el tool-loop en acción
const composer = page.locator("[placeholder*='ensaje'], [placeholder*='IA'], [contenteditable=true]").last();
if (await composer.count()) {
  await composer.click();
  await composer.fill("cuántos contactos tengo");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(12000);
  await page.screenshot({ path: "/root/DOLAN_odoo20/DOLAN_theme/qa/shots/l34-ee-ia-chat.png" });
  const conv = await page.evaluate(() => {
    const msgs = [...document.querySelectorAll("[class*=message], [class*=msg]")].slice(-4)
      .map(m => m.textContent.trim().slice(0, 100));
    return msgs;
  });
  console.log("CONVERSACION:", JSON.stringify(conv));
}
await b.close();
