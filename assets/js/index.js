const setActiveLink = () => {
  let currentUrl = window.location.pathname;
  let splitCurrentUrl = currentUrl.split('/');

  if (splitCurrentUrl.length > 2) {
    if (splitCurrentUrl[1] === 'katalog') {
      $('#a-catalog').addClass('active-link');
    } else if (splitCurrentUrl[1] === 'contact') {
      console.log('a')
      $('#a-contact').addClass('active-link');
    }
  } else {
    if (splitCurrentUrl[1] === "") {
      $('#a-home').addClass('active-link');
    }
  }
};

setActiveLink();