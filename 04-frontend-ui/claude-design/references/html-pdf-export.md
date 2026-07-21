# HTML 导出 PDF 最佳实践

## 问题场景

在浏览器中通过 HTML 生成 PDF 时，常见陷阱：

1. **html2pdf.js 的 `.save()` 被拦截**：在 headless 浏览器或某些安全策略下，自动下载会生成空文件
2. **CDN 依赖不稳定**：html2pdf.js 从 CDN 加载可能失败
3. **图片跨域**：html2canvas 处理外部图片时 CORS 问题导致空白
4. **分页断裂**：表格、卡片在页边被截断

## 推荐方案

### 方案 A：html2pdf.js + Blob 手动下载（前端）

```javascript
function exportPDF() {
  const element = document.getElementById('pdf-content');
  
  const opt = {
    margin: [12, 12, 12, 12],
    filename: 'output.pdf',
    image: { type: 'jpeg', quality: 0.95 },
    html2canvas: {
      scale: 1.5,
      useCORS: true,
      letterRendering: true,
      scrollY: 0,
      windowWidth: element.offsetWidth
    },
    jsPDF: {
      unit: 'mm',
      format: 'a4',
      orientation: 'portrait'
    }
  };

  // 关键：用 toPdf().get('pdf') 获取对象，手动触发下载
  html2pdf().set(opt).from(element).toPdf().get('pdf').then(function(pdf) {
    const blob = pdf.output('blob');
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'output.pdf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}
```

### 方案 B：Puppeteer 服务端生成（Node.js）

```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.goto('file:///path/to/file.html', {
    waitUntil: 'networkidle0',
    timeout: 30000
  });
  await page.waitForTimeout(3000); // 等字体/图片加载
  await page.pdf({
    path: 'output.pdf',
    format: 'A4',
    printBackground: true,
    margin: { top: '15mm', right: '15mm', bottom: '15mm', left: '15mm' }
  });
  await browser.close();
})();
```

### 方案 C：浏览器原生打印（最简单）

```css
@media print {
  .no-print { display: none; }
  body { background: #fff; }
  .card { break-inside: avoid; }
}
```

```javascript
window.print(); // 用户手动选择"保存为 PDF"
```

## 打印优化 CSS

```css
@media print {
  /* 隐藏导航和按钮 */
  .nav, .pdf-btn { display: none !important; }
  
  /* 白底 */
  body { background: #fff !important; }
  
  /* 避免卡片/表格被分页截断 */
  .card, .info-card, table {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  
  /* 章节标题前分页 */
  .section-title {
    page-break-before: auto;
  }
}
```

## 关键配置项

| 配置 | 作用 | 推荐值 |
|------|------|--------|
| `html2canvas.scale` | 分辨率倍数 | 1.5（平衡清晰度与文件大小） |
| `html2canvas.useCORS` | 跨域图片处理 | true |
| `jsPDF.format` | 页面尺寸 | 'a4' |
| `margin` | 页边距 | 12-15mm |
| `printBackground` | 打印背景色 | true |

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| PDF 空白 | html2canvas 渲染失败 | 检查 `useCORS`，降低 `scale` |
| 图片缺失 | 跨域或加载未完成 | 加 `waitForTimeout`，用本地图片 |
| 分页截断 | 没有 break-inside 规则 | 加 `break-inside: avoid` |
| 中文字体缺失 | 系统无中文字体 | Puppeteer 环境安装中文字体 |
| 文件过大 | scale 太高或图片太多 | scale 降到 1.5，压缩图片 |
