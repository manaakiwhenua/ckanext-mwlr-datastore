ckan.module('conditional-field', function ($) {
  return {
    options: { source: null, value: null },
    initialize: function () {
      this.source = this.el.closest('form').find('[name="' + this.options.source + '"]');
      this.source.on('change', this.update.bind(this));
      this.update();
    },
    update: function () {
      this.el.toggle(this.source.val() === this.options.value);
    }
  };
});
