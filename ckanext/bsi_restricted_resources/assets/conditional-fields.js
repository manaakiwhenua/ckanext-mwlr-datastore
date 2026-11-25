ckan.module('conditional-field', function ($) {
  return {
    options: { source: null, value: null },
    initialize: function () {
      this.source = this.el.closest('form').find('[name="' + this.options.source + '"]');
      this.source.on('change', this.update.bind(this));
      this.update();
    },
    update: function () {
      const visible = this.source.val() === this.options.value;
      this.el.toggle(visible);
      if (visible) {
        // Select2 cannot measure the field while its parent is hidden.
        this.el.find('.select2-container').css('width', '100%');
      }
    }
  };
});
