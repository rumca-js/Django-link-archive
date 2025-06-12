const assert = require('assert');
const entries = require('../scripts/entries_library.js');


console.log('---------Entries test---------');


global.getQueryParam = (param) => {
  if (param === 'test') {
    return 'mocked_value';
  }
  return null;
};

global.getDefaultFileName = () => {
  return 'mocked_value';
};

global.escapeHtml = (string) => {
  return 'mocked_value';
};

global.isMobile = () => {
  return false;
};


global.view_display_type = "search-engine";
global.view_show_icons = true;
global.view_small_icons = true;
global.highlight_bookmarks = true;


function testGetEntryTagsEmpty() {
  const entry = {
    link: "https://youtube.com/else",
    title: "title",
    description: "description"
    // no 'tags' field
  };

  const tags = entries.getEntryTags(entry);

  assert.strictEqual(tags, "");
  console.log('✅');
}


function testGetEntryTagsNotEmpty() {
  const entry = {
    link: "https://youtube.com/else",
    title: "title",
    description: "description",
    tags: ["something", "else"],
  };

  const tags = entries.getEntryTags(entry);

  assert.strictEqual(tags, "#something,#else");
  console.log('✅');
}


function testGetEntryListTestStandard() {
  global.view_display_type = "standard";
  global.view_show_icons = true;
  global.view_small_icons = true;

  const entry = {
    link: "https://youtube.com/else",
    title: "title",
    description: "description",
    tags: ["something", "else"],
  };

  const text = entries.getEntryListText(entry);

  assert.ok(typeof text === 'string' && text.length > 0);
  console.log('✅');
}


function testGetEntryListTestGallery() {
  global.view_display_type = "gallery";
  global.view_show_icons = true;
  global.view_small_icons = true;

  const entry = {
    link: "https://youtube.com/else",
    title: "title",
    description: "description",
    tags: ["something", "else"],
  };

  const text = entries.getEntryListText(entry);

  assert.ok(typeof text === 'string' && text.length > 0);
  console.log('✅');
}


function testGetEntryListTestSearchEngine() {

  const entry = {
    link: "https://youtube.com/else",
    title: "title",
    description: "description",
    tags: ["something", "else"],
  };

  const text = entries.getEntryListText(entry);

  assert.ok(typeof text === 'string' && text.length > 0);
  console.log('✅');
}


testGetEntryTagsEmpty();
testGetEntryTagsNotEmpty();
testGetEntryListTestStandard();
testGetEntryListTestGallery();
testGetEntryListTestSearchEngine();
