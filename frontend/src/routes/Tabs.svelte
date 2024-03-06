<script lang="ts">
  export let items: any[] = [];
  export let activeTabValue = 1;

  const handleClick = (tabValue: number) => () => (activeTabValue = tabValue);
</script>

<div class="tabbox">
  <ul>
  {#each items as item}
    <li class={activeTabValue === item.value ? 'active' : ''}>
      <span on:click={handleClick(item.value)}>{item.label}</span>
    </li>
  {/each}
  </ul>
  {#each items as item}
    <div class:hide={activeTabValue !== item.value} class="box">
      <svelte:component this={item.component} {...item.props}/>
    </div>
  {/each}
</div>
<style>
  .tabbox {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
	.box {
		margin-bottom: 10px;
		padding: 0.5em;
    flex-grow: 1;
	}
  .hide {
    display:none;
  }
  ul {
    display: flex;
    flex-wrap: wrap;
    padding-left: 0.5em;
    margin-bottom: 0;
    margin-top: 0.5em;
    list-style: none;
    border-bottom: 1px solid black;
  }
	li {
		margin-bottom: -1px;
	}

  span {
    border: 1px solid transparent;
    border-top-left-radius: 0.25rem;
    border-top-right-radius: 0.25rem;
    display: block;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }

  li.active > span {
    border-color: black black rgb(255, 234, 244);
  }
</style>