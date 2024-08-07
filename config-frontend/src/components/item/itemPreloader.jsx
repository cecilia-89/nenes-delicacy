import './itemPreloader.scss'


window.scrollTo(0,0)

const ItemPreloader = () => {
    return (
        <section className='skeleton-item'>
            <div>
                <a href=""></a>
                <a href=""></a>
                <a href=""></a>
            </div>

            <div>
                <div>
                    <div className="skeleton-image">
                    
                    </div>
                </div>

                <div className='skeleton-item-info'>
                    <div>
                        {[...Array(5)].map((x, index) => (
                            <div key={index}></div>
                        ))}
                    </div>
                </div>  
            </div>
        </section>
    )
}

export default ItemPreloader;