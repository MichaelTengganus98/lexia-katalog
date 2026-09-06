$(document).ready(function () {
  const products = $('#product').offset().top;
  $(document).scroll(function () {
    let scrollPos = $(document).scrollTop();
    if (scrollPos >= products) {
      $('#nav').addClass('light-nav');
    } else if (scrollPos < products) {
      $('#nav').removeClass('light-nav');
    }
  });

  $('#slider').cardSlider({
    slideTag: 'div',
    slideClass: 'slide'
  });

  $('#slider-2').cardSlider({
    slideTag: 'div',
    slideClass: 'slide'
  });
});



