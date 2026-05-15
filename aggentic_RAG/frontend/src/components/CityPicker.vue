<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "选择城市" },
  disabled: { type: Boolean, default: false },
  exclude: { type: String, default: "" }, // 互斥城市，在选择列表中置灰
});

const emit = defineEmits(["update:modelValue"]);

// ======== 中国城市数据 — 按省份分组，覆盖所有地级市 ========
const cityGroups = [
  { letter: "热门",
    cities: ["北京", "上海", "广州", "深圳", "成都", "杭州", "南京", "重庆", "武汉",
             "西安", "苏州", "厦门", "长沙", "青岛", "天津", "昆明", "三亚", "大连",
             "桂林", "丽江", "大理", "张家界", "黄山", "哈尔滨", "海口"] },
  { letter: "直辖市",
    cities: ["北京", "上海", "天津", "重庆"] },
  { letter: "河北",
    cities: ["石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州",
             "廊坊", "衡水", "辛集", "定州", "泊头", "任丘", "黄骅", "河间", "霸州", "三河",
             "遵化", "迁安", "武安", "南宫", "沙河", "涿州", "安国", "高碑店", "平泉", "深州"] },
  { letter: "山西",
    cities: ["太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾",
             "吕梁", "古交", "潞城", "高平", "介休", "原平", "侯马", "霍州", "永济", "河津",
             "孝义", "汾阳"] },
  { letter: "内蒙古",
    cities: ["呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔",
             "乌兰察布", "兴安盟", "锡林郭勒", "阿拉善", "满洲里", "扎兰屯", "牙克石", "根河",
             "额尔古纳", "乌兰浩特", "阿尔山", "二连浩特", "锡林浩特", "丰镇"] },
  { letter: "辽宁",
    cities: ["沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新",
             "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛", "瓦房店", "庄河", "海城", "东港",
             "凤城", "凌海", "北镇", "盖州", "大石桥", "灯塔", "调兵山", "开原", "北票", "凌源", "兴城"] },
  { letter: "吉林",
    cities: ["长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边",
             "延吉", "图们", "敦化", "珲春", "龙井", "和龙", "公主岭", "梅河口", "集安",
             "临江", "大安", "洮南", "扶余", "桦甸", "蛟河", "磐石", "舒兰", "双辽"] },
  { letter: "黑龙江",
    cities: ["哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯",
             "七台河", "牡丹江", "黑河", "绥化", "大兴安岭", "阿城", "双城", "尚志", "五常",
             "讷河", "密山", "虎林", "绥芬河", "宁安", "海林", "穆棱", "同江", "富锦",
             "北安", "五大连池", "安达", "肇东", "海伦"] },
  { letter: "江苏",
    cities: ["南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城",
             "扬州", "镇江", "泰州", "宿迁", "江阴", "宜兴", "邳州", "新沂", "溧阳", "常熟",
             "张家港", "昆山", "太仓", "如皋", "启东", "海安", "仪征", "高邮", "丹阳", "扬中",
             "句容", "靖江", "泰兴", "兴化", "东台"] },
  { letter: "浙江",
    cities: ["杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山",
             "台州", "丽水", "建德", "慈溪", "余姚", "瑞安", "乐清", "海宁", "平湖", "桐乡",
             "诸暨", "嵊州", "江山", "临海", "温岭", "龙泉", "义乌", "东阳", "永康", "兰溪",
             "奉化"] },
  { letter: "安徽",
    cities: ["合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山",
             "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城", "巢湖", "桐城", "天长",
             "明光", "宁国", "广德", "潜山", "怀宁", "凤阳", "寿县"] },
  { letter: "福建",
    cities: ["福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德",
             "福清", "长乐", "永安", "石狮", "晋江", "南安", "龙海", "邵武", "武夷山", "建瓯",
             "漳平", "福鼎", "福安"] },
  { letter: "江西",
    cities: ["南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春",
             "抚州", "上饶", "瑞昌", "乐平", "瑞金", "井冈山", "丰城", "樟树", "高安", "德兴",
             "贵溪"] },
  { letter: "山东",
    cities: ["济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安",
             "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽", "章丘", "胶州", "平度",
             "莱西", "即墨", "滕州", "龙口", "莱阳", "莱州", "蓬莱", "招远", "栖霞", "海阳",
             "青州", "诸城", "寿光", "安丘", "高密", "昌邑", "曲阜", "邹城", "新泰", "肥城",
             "乳山", "荣成", "乐陵", "禹城", "临清", "邹平"] },
  { letter: "河南",
    cities: ["郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳",
             "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店", "济源",
             "巩义", "荥阳", "新密", "新郑", "登封", "偃师", "舞钢", "汝州", "林州", "卫辉",
             "辉县", "沁阳", "孟州", "禹州", "长葛", "邓州", "永城", "项城", "义马", "灵宝"] },
  { letter: "湖北",
    cities: ["武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州",
             "黄冈", "咸宁", "随州", "恩施", "仙桃", "潜江", "天门", "神农架", "大冶", "丹江口",
             "枝江", "宜都", "当阳", "老河口", "枣阳", "宜城", "钟祥", "应城", "安陆", "汉川",
             "石首", "洪湖", "松滋", "麻城", "武穴", "赤壁", "广水", "利川"] },
  { letter: "湖南",
    cities: ["长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳",
             "郴州", "永州", "怀化", "娄底", "湘西", "浏阳", "醴陵", "湘乡", "韶山", "耒阳",
             "常宁", "武冈", "临湘", "汨罗", "津市", "沅江", "资兴", "洪江", "冷水江", "涟源",
             "吉首", "凤凰"] },
  { letter: "广东",
    cities: ["广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名",
             "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州",
             "揭阳", "云浮", "从化", "乐昌", "南雄", "开平", "台山", "恩平", "鹤山", "廉江",
             "雷州", "吴川", "高州", "化州", "信宜", "四会", "英德", "连州", "普宁", "罗定",
             "增城", "阳春", "陆丰", "兴宁"] },
  { letter: "广西",
    cities: ["南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林",
             "百色", "贺州", "河池", "来宾", "崇左", "凭祥", "东兴", "桂平", "北流", "宜州",
             "合山", "岑溪", "荔浦", "靖西"] },
  { letter: "海南",
    cities: ["海口", "三亚", "三沙", "儋州", "五指山", "琼海", "文昌", "万宁", "东方",
             "定安", "屯昌", "澄迈", "临高", "白沙", "昌江", "乐东", "陵水", "保亭", "琼中",
             "洋浦"] },
  { letter: "四川",
    cities: ["成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江",
             "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝",
             "甘孜", "凉山", "都江堰", "彭州", "邛崃", "崇州", "广汉", "什邡", "绵竹", "江油",
             "峨眉山", "阆中", "华蓥", "万源", "简阳", "西昌", "康定", "马尔康"] },
  { letter: "贵州",
    cities: ["贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南", "黔东南", "黔南",
             "清镇", "赤水", "仁怀", "盘州", "兴义", "凯里", "都匀", "福泉", "镇远", "黄平"] },
  { letter: "云南",
    cities: ["昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄",
             "红河", "文山", "西双版纳", "大理", "德宏", "怒江", "迪庆", "安宁", "宣威",
             "弥勒", "芒市", "瑞丽", "腾冲", "香格里拉", "蒙自", "个旧", "开远", "景洪",
             "澄江", "建水", "巍山"] },
  { letter: "西藏",
    cities: ["拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里", "墨脱", "波密",
             "江孜", "亚东", "樟木"] },
  { letter: "陕西",
    cities: ["西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康",
             "商洛", "兴平", "韩城", "华阴", "神木", "府谷", "子长", "彬州", "旬阳", "洛南",
             "黄陵"] },
  { letter: "甘肃",
    cities: ["兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉",
             "庆阳", "定西", "陇南", "临夏", "甘南", "玉门", "敦煌", "临夏市", "合作",
             "华亭", "泾川", "永靖"] },
  { letter: "青海",
    cities: ["西宁", "海东", "海北", "黄南", "海南", "果洛", "玉树", "海西", "德令哈",
             "格尔木", "茫崖"] },
  { letter: "宁夏",
    cities: ["银川", "石嘴山", "吴忠", "固原", "中卫", "灵武", "青铜峡", "同心", "西吉",
             "隆德", "泾源", "彭阳", "中宁", "海原"] },
  { letter: "新疆",
    cities: ["乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉", "博尔塔拉", "巴音郭楞",
             "阿克苏", "克孜勒苏", "喀什", "和田", "伊犁", "塔城", "阿勒泰", "石河子",
             "阿拉尔", "图木舒克", "五家渠", "北屯", "铁门关", "双河", "可克达拉", "昆玉",
             "库尔勒", "奎屯", "乌苏", "伊宁", "莎车", "阜康", "博乐", "阿图什", "塔什库尔干"] },
  { letter: "香港", cities: ["香港", "九龙", "新界", "离岛"] },
  { letter: "澳门", cities: ["澳门", "氹仔", "路环"] },
  { letter: "台湾",
    cities: ["台北", "高雄", "台中", "台南", "基隆", "新竹", "嘉义", "桃园", "新北",
             "宜兰", "花莲", "台东", "屏东", "澎湖", "金门", "连江", "马祖", "彰化", "云林",
             "苗栗", "南投"] },
];

const allCities = computed(() => {
  const list = [];
  for (const g of cityGroups) {
    for (const c of g.cities) {
      if (c !== props.exclude) list.push(c);
    }
  }
  return list;
});

// ======== 面板状态 ========
const show = ref(false);
const search = ref("");
const inputRef = ref(null);
const panelRef = ref(null);
const searchRef = ref(null);

// 过滤后的城市列表
const filtered = computed(() => {
  if (!search.value.trim()) return null; // null 表示不过滤，显示完整分组
  const kw = search.value.trim().toLowerCase();
  const result = [];
  for (const c of allCities.value) {
    if (c.includes(kw) || toPinyin(c).includes(kw)) {
      result.push(c);
    }
  }
  return result;
});

// 拼音首字母
function toPinyin(s) {
  // 简化版拼音映射，仅用于搜索
  const map = {
    "北京": "bj", "上海": "sh", "广州": "gz", "深圳": "sz", "成都": "cd",
    "杭州": "hz", "南京": "nj", "重庆": "cq", "武汉": "wh", "西安": "xa",
    "苏州": "sz", "厦门": "xm", "长沙": "cs", "青岛": "qd", "天津": "tj",
    "昆明": "km", "郑州": "zz", "济南": "jn", "沈阳": "sy", "哈尔滨": "heb",
    "大连": "dl", "福州": "fz", "南昌": "nc", "桂林": "gl", "三亚": "sy",
    "大理": "dl", "丽江": "lj", "海口": "hk", "拉萨": "ls", "贵阳": "gy",
    "合肥": "hf", "宁波": "nb", "无锡": "wx", "温州": "wz", "泉州": "qz",
    "徐州": "xz", "太原": "ty", "长春": "cc", "南宁": "nn", "石家庄": "sjz",
    "兰州": "lz", "西宁": "xn", "银川": "yc", "乌鲁木齐": "wlmq",
    "珠海": "zh", "佛山": "fs", "东莞": "dg", "洛阳": "ly", "开封": "kf",
    "黄山": "hs", "丽江": "lj", "惠州": "huiz", "宜昌": "yc", "扬州": "yz",
  };
  return map[s] || s.toLowerCase();
}

function select(city) {
  emit("update:modelValue", city);
  show.value = false;
  search.value = "";
}

function toggle() {
  if (props.disabled) return;
  show.value = !show.value;
  if (show.value) {
    nextTick(() => {
      searchRef.value?.focus();
    });
  }
}

function onInputClick() {
  if (props.disabled) return;
  show.value = true;
  nextTick(() => {
    searchRef.value?.focus();
  });
}

// 点击外部关闭
function onDocClick(e) {
  if (panelRef.value && !panelRef.value.contains(e.target) &&
      inputRef.value && !inputRef.value.contains(e.target)) {
    show.value = false;
    search.value = "";
  }
}

onMounted(() => document.addEventListener("click", onDocClick));
onUnmounted(() => document.removeEventListener("click", onDocClick));
</script>

<template>
  <div class="city-picker" :class="{ open: show }">
    <!-- 输入框 -->
    <input
      ref="inputRef"
      class="picker-trigger"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      readonly
      @click="onInputClick"
    />
    <span class="picker-arrow" @click="toggle">▼</span>

    <!-- 下拉面板 -->
    <div v-if="show" ref="panelRef" class="picker-panel">
      <!-- 搜索 -->
      <div class="panel-search">
        <input
          ref="searchRef"
          v-model="search"
          class="search-input"
          placeholder="搜索城市（拼音/中文）"
        />
      </div>

      <!-- 搜索结果 -->
      <div v-if="filtered" class="panel-list">
        <button
          v-for="c in filtered"
          :key="c"
          class="city-btn"
          :class="{ active: c === modelValue }"
          @click="select(c)"
        >
          {{ c }}
        </button>
      </div>

      <!-- 分组列表 -->
      <div v-else class="panel-groups">
        <div v-for="g in cityGroups" :key="g.letter" class="city-group">
          <div class="group-letter">{{ g.letter }}</div>
          <div class="group-cities">
            <button
              v-for="c in g.cities"
              :key="c"
              class="city-btn"
              :class="{
                active: c === modelValue,
                dimmed: c === exclude,
              }"
              :disabled="c === exclude"
              @click="select(c)"
            >
              {{ c }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.city-picker {
  position: relative;
  width: 100%;
}

.picker-trigger {
  width: 100%;
  padding: 0.55rem 2rem 0.55rem 0.7rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  cursor: pointer;
  background: #fff;
  transition: border-color 0.15s;
  box-sizing: border-box;
}
.picker-trigger:focus {
  outline: 2px solid var(--color-primary);
  border-color: var(--color-primary);
}
.picker-trigger:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.picker-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.6rem;
  color: #999;
  pointer-events: none;
}

/* 下拉面板 */
.picker-panel {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 200;
  width: 400px;
  max-height: 380px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-search {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid #eef1f5;
  flex-shrink: 0;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: inherit;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.15s;
}
.search-input:focus {
  border-color: var(--color-primary);
}

/* 搜索结果 */
.panel-list {
  padding: 0.5rem 0.75rem;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-content: flex-start;
}

/* 分组 */
.panel-groups {
  overflow-y: auto;
  padding: 0 0.75rem 0.5rem;
}

.city-group {
  border-bottom: 1px solid #f5f6f9;
}
.city-group:first-child {
  border-bottom: 1px solid var(--color-border);
}
.city-group:last-child {
  border-bottom: none;
}

.group-letter {
  font-weight: 700;
  font-size: 0.8rem;
  color: var(--color-primary);
  padding: 0.5rem 0 0.3rem;
  position: sticky;
  top: 0;
  background: #fff;
}

.group-cities {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0.25rem 0 0.5rem;
}

/* 城市按钮 */
.city-btn {
  padding: 0.3rem 0.55rem;
  border: none;
  border-radius: 6px;
  font-size: 0.82rem;
  font-family: inherit;
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.12s, color 0.12s;
}
.city-btn:hover:not(:disabled) {
  background: #eaf2ff;
  color: var(--color-primary);
}
.city-btn.active {
  background: var(--color-primary);
  color: #fff;
}
.city-btn.dimmed {
  color: #ccc;
  cursor: default;
}
</style>
