function displayPhotoModal(element) {
    let id = element.id;
    let selector = `#img-${id}`;
    $(selector).modal();
}