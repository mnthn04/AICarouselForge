class CarouselEditor {
    constructor() {
        this.stage = null;
        this.layer = null;

        this.currentSlide = 0;
        this.slides = [];

        this.backgroundNode = null;
        this.titleNode = null;
        this.descNode = null;

        this.init();
    }

    async init() {
        await this.initKonva();
        await this.loadSlides();
        this.bindInputs();
    }

    async initKonva() {
        const container = document.getElementById('konvaContainer');

        this.stage = new Konva.Stage({
            container: 'konvaContainer',
            width: container.clientWidth,
            height: container.clientHeight
        });

        this.layer = new Konva.Layer();
        this.stage.add(this.layer);
    }

    async loadSlides() {
        this.slides = [
            {
                id: 1,
                title: 'Welcome to AI Carousels',
                description: 'Create stunning carousels with AI',
                backgroundColor: '#ffffff',
                fontColor: '#000000'
            },
            {
                id: 2,
                title: 'Fast & Simple',
                description: 'Build content in minutes',
                backgroundColor: '#f8fafc',
                fontColor: '#1e293b'
            }
        ];

        this.renderSlide(0);
    }

    renderSlide(index) {
        this.layer.destroyChildren();

        const slide = this.slides[index];
        const w = this.stage.width();
        const h = this.stage.height();

        this.backgroundNode = new Konva.Rect({
            width: w,
            height: h,
            fill: slide.backgroundColor
        });

        this.titleNode = new Konva.Text({
            x: w / 2,
            y: h * 0.3,
            text: slide.title,
            fontSize: 48,
            fill: slide.fontColor,
            width: w * 0.8,
            align: 'center'
        });
        this.titleNode.offsetX(this.titleNode.width() / 2);

        this.descNode = new Konva.Text({
            x: w / 2,
            y: h * 0.5,
            text: slide.description,
            fontSize: 24,
            fill: slide.fontColor,
            width: w * 0.7,
            align: 'center'
        });
        this.descNode.offsetX(this.descNode.width() / 2);

        this.layer.add(this.backgroundNode, this.titleNode, this.descNode);
        this.layer.batchDraw();

        this.syncInputs(slide);
    }

    syncInputs(slide) {
        document.getElementById('slideTitle').value = slide.title;
        document.getElementById('slideDescription').value = slide.description;
        document.getElementById('bgColor').value = slide.backgroundColor;
        document.getElementById('fontColor').value = slide.fontColor;
    }

    bindInputs() {
        document.getElementById('slideTitle').addEventListener('input', e => {
            const slide = this.slides[this.currentSlide];
            slide.title = e.target.value;
            this.titleNode.text(slide.title);
            this.layer.batchDraw();
        });

        document.getElementById('slideDescription').addEventListener('input', e => {
            const slide = this.slides[this.currentSlide];
            slide.description = e.target.value;
            this.descNode.text(slide.description);
            this.layer.batchDraw();
        });

        document.getElementById('bgColor').addEventListener('input', e => {
            const slide = this.slides[this.currentSlide];
            slide.backgroundColor = e.target.value;
            this.backgroundNode.fill(slide.backgroundColor);
            this.layer.batchDraw();
        });

        document.getElementById('fontColor').addEventListener('input', e => {
            const slide = this.slides[this.currentSlide];
            slide.fontColor = e.target.value;
            this.titleNode.fill(slide.fontColor);
            this.descNode.fill(slide.fontColor);
            this.layer.batchDraw();
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new CarouselEditor();
});
