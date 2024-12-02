
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

let navigationBtns = document.querySelectorAll('li');
let header_bar_subBlocks = document.querySelector('#header_bar_subBlock');
let blur_overlay = document.querySelector('.blurOverlay');

// GSAP
 // use a script tag or an external JS file
 document.addEventListener("DOMContentLoaded", (event) => {
    gsap.registerPlugin(Flip,ScrollTrigger,Observer,ScrollToPlugin,TextPlugin,RoughEase,ExpoScaleEase,SlowMo)
    // gsap code here!
});

(function() {
    Galleria.loadTheme('https://cdnjs.cloudflare.com/ajax/libs/galleria/1.5.7/themes/classic/galleria.classic.min.js');
    Galleria.run('.galleria');
}());


if (Galleria) { console.log("Galleria properly run") }



navigationBtns.forEach(function(btn) {
    console.log(btn);
    btn.addEventListener('mouseover', function() {
        // We'll remove it when we quit the header
        header_bar_subBlocks.classList.add('extended');
        // Blur the background
        blur_overlay.classList.remove('hidden');
    })
});

header.addEventListener('mouseleave', function() {
    header_bar_subBlocks.classList.remove('extended');
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


gsap.from('#phone2', {
    duration: 5,
    opacity: 0,
    ease: 'ease-in'
});


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



  