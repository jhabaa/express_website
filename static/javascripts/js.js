
let burger = document.querySelector('#burger');
let header = document.querySelector('#header');
let body = document.querySelector('#body');
let ADS = document.querySelector('#ADS');
let lang_btn = document.querySelector('#lang');
let navigation = document.querySelector('#navigation');
let main = document.querySelector('#main');
let footer = document.querySelector('#footer');
let navigation_links = document.querySelectorAll('#nav_links');
var active_category = document.querySelector('#active_category');
var category_btn = document.querySelectorAll('.cat_btn');
var logo = document.querySelector('.logos');
var photowall = document.querySelector('.photowall');
let photos = document.querySelectorAll('.photo');
let scroller_in = document.querySelector('.scroller_in');

let navigationBtns = document.querySelectorAll('.nav_link');
let header_bar_subBlocks = document.querySelector('#header_bar_subBlock');
let blur_overlay = document.querySelector('.blurOverlay');

let services = document.querySelectorAll('.service');
let store_cards = document.querySelectorAll('.store_card');
let sublinks = document.querySelectorAll('.sublink');
let pricing_links = document.getElementById('pricing_links');
let phonesPictures = document.querySelectorAll('.phone');

//Numbers 
let exp_years = document.querySelector('#years_exp');
let partners = document.querySelector('#partners');
var numbers_values = {years:0,
    partners:0,
}
//engagement cards 
let engagement_card = document.querySelector('#engagement-card');
if (engagement_card) { 
    console.log(engagement_card);
    VanillaTilt.init(engagement_card, {
        max: 25,
        speed: 400,
        glare: true,
        "max-glare": 0.5,
    });
}

//let animate this 
var options = {
    root: null,
    rootMargin: '0px',
    threshold: 0.5
}
let creationDate =  new Date('Jan 01, 97 00:00:00')
let today = new Date();
let numbers_animation = anime ({
    targets : numbers_values,
    years: today.getFullYear() - creationDate.getFullYear(),
    partners: "300+",
    direction: 'forwards',
    round: 1,
    easing: 'easeInOutExpo',
    autoplay:false,
    update: function(){
        exp_years.innerHTML = numbers_values.years;
        partners.innerHTML = numbers_values.partners;
    }
});
var callback = function(entries, observer){
    entries.forEach(entry => {
        if (entry.isIntersecting){
            numbers_animation.play();
        }else {
            numbers_animation.pause();
        }
    });
}
var oberserver = new IntersectionObserver(callback, options);
if (exp_years && partners){
    oberserver.observe(exp_years);
}

// Hide phones image when we scroll a bit 
phonesPictures.forEach(function(phone){
    window.addEventListener('scroll', function(){
        if (window.scrollY > 10){
            phone.classList.add('hidden');
        }else {
            phone.classList.remove('hidden');
        }
    });
});

//Init AOS
AOS.init();

// GSAP
 // use a script tag or an external JS file
 document.addEventListener("DOMContentLoaded", (event) => {
    gsap.registerPlugin(Flip,ScrollTrigger,Observer,ScrollToPlugin,TextPlugin,RoughEase,ExpoScaleEase,SlowMo, ScrambleTextPlugin)
    // gsap code here!

    // load splide 

    
});

if (document.querySelector('.splide')){
    var splide = new Splide( '.splide', {
        type: 'loop',
        rewind: true,
        direction: 'btt',
        pagination : false,
        autoplay: true,
        interval: 5000,
        arrows: false,
        align: 'center',
        focus: 'center',
        autowidth: true,

        breakpoints: {
            650: {
                perPage: 1,
            },
            1200: {
                perPage: 2,
            }
        }
    } ).mount();
}

// First, if we have services, activat the first one 
if (services.length > 0) {
    services.item(0).classList.add('active');
    // Now set the query when we hover the rest 
    services.forEach(function(service) {
        service.addEventListener('mouseover', function() {
            services.forEach(function(service) {
                service.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
}
// Set action when we over the services cards 

// Now for store cards
if (store_cards.length > 0) {
    store_cards.forEach(function(card) {
        card.addEventListener('mouseover', function() {
            store_cards.forEach(function(card) {
                card.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
}


if (sublinks.length > 0) {
    sublinks.forEach(function(sublink) {
        // When we hover a link, we'll add it to sublinks links
        sublink.addEventListener('mouseover', function() {
            if (pricing_links){
                sublinks_links.innerHTML = this.innerHTML;
            }
            
        });
    });
}

navigationBtns.forEach(function(btn) {
    console.log(btn);
    btn.addEventListener('mouseover', function() {
        // Get the second child of the btn
        // We'll remove it when we quit the header
        btn.classList.remove('hidden');
        // Blur the background
        // Only if the node has more than one child
        if (btn.childElementCount <= 1){return}
        blur_overlay.classList.remove('hidden');
    })
    btn.addEventListener('mouseleave', function() {
        // Get the second child of the btn
        // We'll remove it when we quit the header
        btn.classList.add('hidden');
        // Blur the background
        blur_overlay.classList.add('hidden');
    });
});

header.addEventListener('mouseleave', function() {

    blur_overlay.classList.add('hidden');
}
);

/* let navigation_extension = gsap.fromTo(navigation_links, {

},{
    duration: 1,
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
    paddingTop: '50px',
    height: '100%',
    fontSize: '7vh',
    filter: 'blur(0px)',
    webkitFilter: 'blur(0px)',
    ease: 'ease-in-out'
}); 
/* 
let lang_extension = gsap.fromTo('#lang', {
    position: 'absolute',
    maxHeight: '100px',
    top:'unset',
    right:"unset",
    gap:"20px",

},
    {
    duration: 1,
    display: 'flex',
    width: '100%',
    top: '80px',
    fontSize: '4vh',
    ease: 'ease-in-out'
}); */

let logo_extension = gsap.to(logo, {
    duration: 1,
    position: 'absolute',
    top: '10px',
    left: '40vw',
    ease: 'bounce'
});


if (exp_years){
    gsap.to(exp_years, {duration: 2, scrambleText:{text:"10", chars:"0123456789", speed:0.3}});
}


/*
a.forEach((el)=>{
    const cpImage = el.cloneNode(true);
    cpImage.setAttribute("aria-hidden", true);
    scroller_in.appendChild(cpImage);
})
*/
/*
photos.forEach(function(photo) {
    gsap.fromTo(photo, {
        translateX: 0
    }, {
        duration: imgWidth * 6 / 50,
        translateX: -imgWidth * photowall.childElementCount,
        ease: 'linear',
        repeat: -1,
        onUpdate: function() {
            //get the current position of the photo
            let x = photo.getBoundingClientRect().left;
            //if the photo is out of the screen
            if (x < 0){
                //move it to the end of the photowall
                photowall.appendChild(photo);
                
            }
        }
    });
});

*/
// Add images to the photo wall
//watch photos






// Function to add images to the photo wall
function addImage() {
    photos.forEach(function(photo) {
        let newPhoto = photo.cloneNode(true);
        photowall.appendChild(newPhoto);
    });
}


function scrollManagement(){
        body.classList.toggle('stop');
    //navigation.classList.toggle('hide');
        main.classList.toggle('hide');
        footer.classList.toggle('hide');
}
/* navigation_extension.pause(); */
/* lang_extension.pause(); */
logo_extension.pause();
// Header animations
/// Bar extender

var header_bar_status = false;
var tl_header = gsap.timeline({
    onComplete: ()=>{
        header_bar_status = !header_bar_status;
    },
    yoyo: true,
});






category_btn.forEach(function(btn) {
    btn.addEventListener('click', function() {
        category_btn.forEach(function(btn) {
            btn.classList.remove('active');
            unselectCat(btn.innerHTML);
        });
        this.classList.add('active');
        selectCat(btn.innerHTML);
    });
});
if (category_btn.length > 0){
    category_btn.item(0).classList.add('active');
    selectCat(category_btn.item(0).innerHTML);
}

burger.onclick = function() {
    //header.classList.toggle('hide');
    //header.classList.toggle('extended');
    if (burger.classList.contains('extended') && tl_header.progress() > 0) {
        header.classList.remove('extended');
        navigation.classList.add('hide');
        /* navigation_extension.reverse(); */
        /* lang_extension.reverse(); */

       //logo_extension.reverse();
    }else {
        header.classList.add('extended');
        navigation.classList.remove('hide');
        /* navigation_extension.play(); */
        /* lang_extension.play(); */
       // logo_extension.play();
    }
/*     if (tl_header.progress() > 0) {
        tl_header.reverse();
        navigation_extension.reverse();
        lang_extension.reverse();
        logo_extension.reverse();
    }else {
        tl_header.play();
        navigation_extension.play();
        lang_extension.play();
        logo_extension.play();
    } */
   burger.classList.toggle('extended');
   scrollManagement();

}

lang_btn.onclick = function() {
    lang_btn.classList.toggle('extended');
}


function selectCat(selectedCat) {
   console.log(typeof(selectedCat));
   var selectedCategory = document.querySelector('#'+selectedCat.trim());
   selectedCategory.classList.add('active');
}

function unselectCat(selectedCat) {
    var selectedCategory = document.querySelector('#'+selectedCat.trim());
    selectedCategory.classList.remove('active');
}



  