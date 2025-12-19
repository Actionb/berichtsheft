/*
 This script copies the contents of fields 'q2' and 'datum2' into fields 'q' 
 and 'datum_start_0' respectively when the user types in them.

 This synchronizes the search fields with the offcanvas filter inputs.
*/
document.addEventListener('DOMContentLoaded', function() {
    const q2 = document.getElementById('id_q2');
    const datum2 = document.getElementById('id_datum2');
    const q = document.getElementById('id_q');
    const datum_start_0 = document.getElementById('id_datum_start_0');

    q2.addEventListener('input', function() {
        q.value = q2.value;
    });

    datum2.addEventListener('input', function() {
        datum_start_0.value = datum2.value;
    });
});