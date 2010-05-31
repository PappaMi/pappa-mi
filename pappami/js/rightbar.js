    var locations = {};

    function load() {
      var map = new GMap2(document.getElementById("map"));
      map.addControl(new GSmallMapControl());
      map.setCenter(new GLatLng(45.4636889,9.1881408), 10);
      
      GDownloadUrl("/map", function(data) {
        var xml = GXml.parse(data);
        var markers = xml.documentElement.getElementsByTagName("marker");
        for (var i = 0; i < markers.length; i++) {
          var name = markers[i].getAttribute("nome");
          var address = markers[i].getAttribute("indirizzo");
          var type = markers[i].getAttribute("tipo");
          var latlng = new GLatLng(parseFloat(markers[i].getAttribute("lat")),
                                  parseFloat(markers[i].getAttribute("lon")));
          var store = {latlng: latlng, name: name, address: address, type: type};
          var latlngHash = (latlng.lat().toFixed(6) + "" + latlng.lng().toFixed(6));
          latlngHash = latlngHash.replace(".","").replace(".", "").replace("-","");
          if (locations[latlngHash] == null) {
            locations[latlngHash] = []
          }
          locations[latlngHash].push(store);
        }
        for (var latlngHash in locations) {
          var stores = locations[latlngHash];
          if (stores.length > 1) {
            map.addOverlay(createClusteredMarker(stores));
          } else {
            map.addOverlay(createMarker(stores));
          }
         }
      });
    }

    function createMarker(stores) {
      var store = stores[0];
      var newIcon = MapIconMaker.createMarkerIcon({width: 16, height: 16, primaryColor: "#0000ff"});
      var marker = new GMarker(store.latlng, {icon: newIcon});
      /*var html = "<b>" + store.name + "</b> <br/>" + store.address;
      GEvent.addListener(marker, 'click', function() {
        marker.openInfoWindowHtml(html);
      });*/
      return marker;
    }

    function createClusteredMarker(stores) {
      var newIcon = MapIconMaker.createMarkerIcon({width: 24, height: 24, primaryColor: "#0000ff"});
      var marker = new GMarker(stores[0].latlng, {icon: newIcon});
      var html = "";
      for (var i = 0; i < stores.length; i++) {
        html += "<b>" + stores[i].name + "</b> <br/>" + stores[i].address + "<br/>";
      }
      GEvent.addListener(marker, 'click', function() {
        marker.openInfoWindowHtml(html);
      });
      return marker;
    }
    
    window.onload = load;
    window.onunload = GUnload;