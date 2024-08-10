const pow = Math.pow;
const sqrt = Math.sqrt;
const atan = Math.atan;
const abs = Math.abs;
const max = Math.max;
const PI = Math.PI;

let contactUsMap;

window.onload = function () {
    const navSections = new mainNs.NavigableSections('header>ul>li>a[href*="#"]', 'section');
    const fb = document.getElementById('front-banner');
    if (fb !== null) {
        const frontBanner = new mainNs.FrontBanner(document.getElementById('front-banner'));
    }

    // TODO: Finish
    // document.querySelector('#order-sheet input[type="tel"]').addEventListener('input', function (event) {
    //     let s = Array.from(event.target.value).filter(e => numbers.includes(e));
    //     let res = ['+'];
    //     for (let i = 0; i < s.length; i++) {
    //         const extraChar = maskExtraCharacters.get(Math.min(s.length, 14) - i);
    //         if (!(extraChar === undefined)) {
    //             res.push(extraChar);
    //         } 
    //         res.push(s[i]);
    //     }
    //     event.target.value = res.join('');
    // });

    const contactUsMapWrapper = document.getElementById('contact-us-map-wrapper');
    if (contactUsMapWrapper !== null) {
        const contactUsMap = new ymaps.Map('contact-us-map', {
            center: [55.598755, 38.119908],
            zoom: 12
        });

        contactUsMap.controls.add('scaleLine');
        contactUsMap.controls.add('zoomControl');
        contactUsMap.geoObjects.add(new ymaps.Placemark([55.598755, 38.119908]));

        contactUsMapWrapper.addEventListener('dblclick', () => contactUsMapWrapper.classList.add('contact-us-map-wrapper-active'));
    }

    mainNs.initFlyIns();
    mainNs.initDragSolid();
    mainNs.initPolarMouseTrackers();
    // mainNs.initLateIntersectionObservingElements();
}

window.mainNs =
{
    PMT_RECALCULATION_THROTTLE_DURATION_MS: 60,

    NavigableSections: function (linkSelector, sectionSelector = 'section', scrollObservable = document.body, activeClassName = 'active') {
        this.navigableSectionLinks = Array.from(document.querySelectorAll(linkSelector))
            .filter(e => e.href.includes('#'))
            .map(e => ({ sectionId: e.href.split("#").at(-1), target: e }));
        this.navigableSections = Array.from(document.querySelectorAll(sectionSelector))
            .filter(e => this.navigableSectionLinks.some(l => l.sectionId == e.id));

        this.sectionFocusingLine = window.innerHeight / 3;

        this.updateActiveSection = function () {
            if (this.navigableSections.length == 0) {
                return;
            }

            const f = this.sectionFocusingLine;
            let closestDistVal = Infinity;
            let closestDistSection;

            for (let i of this.navigableSections) {
                let r = i.getBoundingClientRect();
                r = r.height > 15 ? new DOMRect(r.x, r.y + 5, r.width, r.height - 5) : r;
                const currentDist = Math.min(Math.abs(r.top - f), Math.abs(r.bottom - f));

                if (currentDist < closestDistVal) {
                    closestDistVal = currentDist;
                    closestDistSection = i;
                }
            }

            const closestDistId = closestDistSection.id;

            for (let i of this.navigableSectionLinks) {
                if (i.sectionId == closestDistId) {
                    i.target.classList.add(activeClassName);
                    // i.target.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                } else {
                    i.target.classList.remove(activeClassName);
                }
            }
        }

        this.updateActiveSection();

        console.log(this)

        scrollObservable.addEventListener('scroll', this.updateActiveSection.bind(this));
    },

    FrontBanner: function (frontBanner) {
        Object.assign(this, { frontBanner });

        this.doAutoScrollFrontBanner = true;
        this.snapGallery = frontBanner.querySelector('.snap-gallery');
        this.prevButton = frontBanner.querySelector('.prev');
        this.nextButton = frontBanner.querySelector('.next');
        this.frontTitles = frontBanner.querySelectorAll('.front-text');

        this._isBigTitleShown = true;
        this._firstChild = frontBanner.querySelector('.snap-gallery>*:first-child');

        this.prevButton.onmouseenter = this.nextButton.onmouseenter = (event) => {
            this.doAutoScrollFrontBanner = false;
        }

        this.prevButton.onmouseleave = this.nextButton.onmouseleave = (event) => {
            this.doAutoScrollFrontBanner = true;
        }

        this.prevButton.onclick = () => {
            this.snapGallery.scroll(this.snapGallery.scrollLeft - 0.9 * this._firstChild.clientWidth, 0);
        };
        this.nextButton.onclick = () => {
            this.snapGallery.scroll(this.snapGallery.scrollLeft + 0.9 * this._firstChild.clientWidth, 0);
        };

        this.snapGallery.onscroll = event => {
            if (this.snapGallery.scrollLeft > 5) {
                if (this._isBigTitleShown) {
                    this._isBigTitleShown = false;
                    this.frontTitles.forEach((e) => {
                        e.style.opacity = '0';
                        e.style.transform = "translateY(5%)";
                    });
                }
            } else {
                if (!this._isBigTitleShown) {
                    this._isBigTitleShown = true;
                    this.frontTitles.forEach((e) => {
                        e.style.opacity = '1';
                        e.style.transform = "translateY(0)";
                    });
                }
            }
        }

        this.scrollToNext = function () {
            if (this.doAutoScrollFrontBanner) {
                mainNs.horizontalCycleScroll(this.snapGallery, 0.9 * this._firstChild.clientWidth);
            }
            setTimeout(this.scrollToNext, 7000);
        }

        setTimeout(this.scrollToNext.bind(this), 7000);
    },

    safeCheckIntersection(ratio, intersectionObserverEntry) {
        if (intersectionObserverEntry.boundingClientRect.height / intersectionObserverEntry.rootBounds.height + 0.1 > 1) {
            return intersectionObserverEntry.intersectionRect.height / intersectionObserverEntry.rootBounds.height > ratio;
        } else {
            return intersectionObserverEntry.intersectionRect.height / intersectionObserverEntry.boundingClientRect.height > ratio;
        }
    },

    throttle(callback, durationMs) {
        let start = Date.now();
        return function (...args) {
            let now = Date.now();
            if (start + durationMs <= now) {
                callback(...args);
                start = now;
            }
        }
    },

    horizontalCycleScroll(element, step) {
        if (element.scrollWidth < element.scrollLeft + element.clientWidth + step) {
            element.scroll(0, 0);
        } else {
            element.scroll(element.scrollLeft + step, 0);
        }
    },

    initFlyIns() {
        const launchFlyInTransition = function (element, className) {
            element.style.transitionDelay = (100 + element.offsetLeft / window.visualViewport.width * 300).toString() + "ms";
            element.style.transitionDuration = (500 + (1 - element.offsetLeft / window.visualViewport.width) * 200).toString() + "ms";
            element.classList.add(className);
        }

        let flyInIntersectionObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(e => {
                if (e.intersectionRatio > 0.3) {
                    if (e.target.classList.contains("fly-in-from-left")) {
                        launchFlyInTransition(e.target, "fly-in-from-left-on");
                    } else if (e.target.classList.contains("fly-in-from-right")) {
                        launchFlyInTransition(e.target, "fly-in-from-right-on");
                    }
                }
            });
        },
            {
                threshold: 0.5
            });

        document.querySelectorAll(".fly-in-from-left, .fly-in-from-right").forEach((e) => { flyInIntersectionObserver.observe(e); })
    },

    initLateIntersectionObservingElements() {
        let intersectionObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(e => {
                if (e.intersectionRatio > 0.4) {
                    e.target.classList.add("observe-intersection-40-active");
                }
            });
        },
            {
                threshold: 0.3
            });

        document.querySelectorAll(".observe-intersection-40").forEach(e => { intersectionObserver.observe(e); });
    },

    initDragSolid() {
        document.querySelector('.drag-solid').addEventListener('ondragstart', e => e.preventDefault());
    },

    _handlePolarMouseTrackerMouseEvent(e, elems) {
        for (const i of elems) {
            const rect = i.getBoundingClientRect()
            // Mouse coordinates relative to the center of the element "i"
            const localPointerX = e.clientX - rect.x - rect.width / 2;
            const localPointerY = e.clientY - rect.y - rect.height / 2;
            const distance = sqrt(pow(localPointerX, 2) + pow(localPointerY, 2));
            i.style.setProperty('--pmt-distance', distance);
            i.style.setProperty('--pmt-angle', atan(localPointerY / localPointerX) + (localPointerX < 0 ? PI : 0));
            i.style.setProperty('--pmt-exp-percentage-x', max(0, -pow(0.65, abs(localPointerX) / rect.width - 0.15) + 1));
            i.style.setProperty('--pmt-exp-percentage-y', max(0, -pow(0.65, abs(localPointerY) / rect.height - 0.15) + 1));
        }
    },

    initPolarMouseTrackers() {
        const elems = document.querySelectorAll('.polar-mouse-tracker');
        document.addEventListener('mousemove', mainNs.throttle((e) => mainNs._handlePolarMouseTrackerMouseEvent(e, elems), mainNs.PMT_RECALCULATION_THROTTLE_DURATION_MS));
    },

    showModalPopup(modalPopup) {
        modalPopup.classList.add('modal-popup-display');
        setTimeout(() => modalPopup.classList.remove('modal-popup-hide'), 20);
    },

    hideModalPopup(modalPopup) {
        modalPopup.classList.add('modal-popup-hide');
        setTimeout(() => {
            if (Array.from(modalPopup.classList).includes('modal-popup-hide')) {
                modalPopup.classList.remove('modal-popup-display');
            }
        }, 1200);
    }
};