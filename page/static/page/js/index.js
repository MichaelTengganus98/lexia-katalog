const setCurrentCatalogPage = () => {
  let currentUrl = window.location.pathname;
  
  $('#list-catalog a[href="' + currentUrl + '"]').addClass('active');
};

setCurrentCatalogPage();