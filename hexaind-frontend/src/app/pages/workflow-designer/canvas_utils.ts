export class CanvasUtils {
  static DrawSegmentedPath(
    ctx: CanvasRenderingContext2D,
    startPoint: { x: number; y: number },
    endPoint: { x: number; y: number },
  ): void {
    ctx.beginPath();
    ctx.moveTo(startPoint.x, startPoint.y);

    if (
      Math.abs(startPoint.x - endPoint.x) > Math.abs(startPoint.y - endPoint.y)
    ) {
      const midX = (startPoint.x + endPoint.x) / 2;
      ctx.lineTo(midX, startPoint.y);
      ctx.lineTo(midX, endPoint.y);
    } else {
      const midY = (startPoint.y + endPoint.y) / 2;
      ctx.lineTo(startPoint.x, midY);
      ctx.lineTo(endPoint.x, midY);
    }

    ctx.lineTo(endPoint.x, endPoint.y);
    ctx.stroke();
  }

  static drawCurvedArrow(
    ctx: CanvasRenderingContext2D,
    startPoint: { x: number; y: number },
    endPoint: { x: number; y: number },
  ): void {
    // context.clearRect(0, 0, this.canvas.nativeElement.width, this.canvas.nativeElement.height);

    ctx.beginPath();

    const controlPointX = (startPoint.x + endPoint.x) / 2;
    const controlPointY = Math.min(startPoint.y, endPoint.y) - 50;

    ctx.moveTo(startPoint.x, startPoint.y);
    ctx.quadraticCurveTo(controlPointX, controlPointY, endPoint.x, endPoint.y);

    // Draw arrowhead
    this.drawArrowhead(ctx, startPoint, endPoint, controlPointX, controlPointY);

    ctx.strokeStyle = 'black';
    ctx.lineWidth = 2;
    ctx.stroke();
  }
  static drawArrowhead(
    ctx: CanvasRenderingContext2D,
    startPoint: { x: number; y: number },
    endPoint: { x: number; y: number },
    controlPointX: number,
    controlPointY: number,
  ): void {
    const angle = Math.atan2(
      endPoint.y - controlPointY,
      endPoint.x - controlPointX,
    );
    const arrowSize = 10;

    ctx.lineTo(endPoint.x, endPoint.y);
    ctx.lineTo(
      endPoint.x - arrowSize * Math.cos(angle - Math.PI / 6),
      endPoint.y - arrowSize * Math.sin(angle - Math.PI / 6),
    );
    ctx.moveTo(endPoint.x, endPoint.y);
    ctx.lineTo(
      endPoint.x - arrowSize * Math.cos(angle + Math.PI / 6),
      endPoint.y - arrowSize * Math.sin(angle + Math.PI / 6),
    );
  }

  static DrawHollowCircle(
    ctx: CanvasRenderingContext2D | null = null,
    x: number,
    y: number,
    radius: number,
    color: string,
  ) {
    if (ctx != null) {
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = 'transparent'; // Make the circle hollow
      ctx.strokeStyle = color; // Pink border color
      ctx.lineWidth = 2; // Border width
      ctx.stroke(); // Draw the circle
    }
  }

  static TruncateText(
    ctx: CanvasRenderingContext2D,
    text: string,
    x: number,
    y: number,
    maxWidth: number,
  ): void {
    let textWidth = ctx.measureText(text).width;
    if (textWidth <= maxWidth) {
      ctx.fillText(text, x, y);
    } else {
      let truncatedText = text;
      while (textWidth > maxWidth && truncatedText.length > 0) {
        truncatedText = truncatedText.substring(0, truncatedText.length - 1);
        textWidth = ctx.measureText(truncatedText + '...').width;
      }
      ctx.fillText(truncatedText + '...', x, y);
    }
  }

  static WrapText(
    context: CanvasRenderingContext2D,
    text: string,
    x: number,
    y: number,
    maxWidth: number,
    lineHeight: number,
  ) {
    let words = text.split(' ');
    let line = '';

    for (let n = 0; n < words.length; n++) {
      let testLine = line + words[n] + ' ';
      let metrics = context.measureText(testLine);
      let testWidth = metrics.width;

      if (testWidth > maxWidth) {
        context.fillText(line, x, y);
        line = words[n] + ' ';
        y += lineHeight;
      } else {
        line = testLine;
      }
    }

    context.fillText(line, x, y);
  }
}
