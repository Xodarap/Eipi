(function gentrack(){
	var $text = $('textarea[name="text"]:first');
	$text.val($text.val() + ' (link text)[http://www.meatlessmonday.com?t={{id}}]');
})();