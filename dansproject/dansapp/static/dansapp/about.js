document.addEventListener('DOMContentLoaded', function() {
    
    let controller = new ScrollMagic.Controller();
    let timeline = new TimelineMax();

    timeline
        //.to('.pi', 3, { y: -500 })
        .fromTo('.pi', 3, { y: -50 }, { y:-1000, duration: 3 })
        //.to('.plates', 3, { y: -200 }, '-=3')
        .fromTo('.plates', 3, { y: -50 }, { y:-700, duration: 3 }, '-=3')
        //.to('.bg', 3, { y: 50 }, '-=3')
        .fromTo('.bg', 3, { y: -50 }, { y:0, duration: 3 }, '-=3')

        .to('.content', 3, { top:'0%' }, '-=3')

        .fromTo('.navbar', {opacity:0}, {opacity:1, duration: 3}, '-=3')
        .fromTo('.navbar', 3, { y: -56 }, { y:0, duration: 3 }, '-=3')

        .fromTo('.main-title', {opacity:0}, {opacity:1, duration: 2.5}, '-=2.5')
        .fromTo('.main-title', {y:500}, {y:0, duration: 2.5}, '-=2.5')

        .to('.main-title', 1, {opacity:0})
        .to('.main-title', 0, {display:'none'})

        .fromTo('.row-1-head', {y:1000}, {y:0, duration: 2})
        .fromTo('.row-2-head', {y:1000}, {y:0, duration: 2}, '-=1')
        .fromTo('.row-3-head', {y:1000}, {y:0, duration: 2}, '-=1')
        .fromTo('.row-4-head', {y:1000}, {y:0, duration: 2}, '-=1')

        .fromTo('.row-1-body', {opacity:0}, {opacity:1, duration: 2})
        .fromTo('.row-2-body', {opacity:0}, {opacity:1, duration: 2}, '-=2')
        .fromTo('.row-3-body', {opacity:0}, {opacity:1, duration: 2}, '-=2')
        .fromTo('.row-4-body', {opacity:0}, {opacity:1, duration: 2}, '-=2')

        .fromTo('.scroll-to-top', {opacity:0}, {opacity:1, duration: 2})

        let scene = new ScrollMagic.Scene({
            triggerElement: 'section',
            duration: '500%',
            triggerHook: 0,
        })
        .setTween(timeline)
        .setPin('section')
        .addTo(controller);

});