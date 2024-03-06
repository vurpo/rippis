<script>
	import Ripper from './Ripper.svelte';
	import Tabs from './Tabs.svelte';

	let rippers = [
		{
			label: "Ripper 1",
			value: 1,
			component: Ripper,
			props: {
				endpoint: "ws://anka:9999",
				name: "1"
			}
		},
		// {
		// 	label: "Ripper 2",
		// 	value: 2,
		// 	component: Ripper,
		// 	props: {
		// 		endpoint: "ws://192.168.2.10:9992",
		// 		name: "2"
		// 	}
		// },
		// {
		// 	label: "Ripper 3",
		// 	value: 3,
		// 	component: Ripper,
		// 	props: {
		// 		endpoint: "ws://192.168.2.10:9993",
		// 		name: "3"
		// 	}
		// },
		// {
		// 	label: "Ripper 4",
		// 	value: 4,
		// 	component: Ripper,
		// 	props: {
		// 		endpoint: "ws://192.168.2.10:9994",
		// 		name: "4"
		// 	}
		// }
	];
</script>

<svelte:head>
	<title>Rippistä :D</title>
	<meta name="description" content="CD ripper interface" />
</svelte:head>

<Tabs items={rippers} />

<style>
</style>
